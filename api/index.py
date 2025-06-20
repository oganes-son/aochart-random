import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import re
import traceback

app = Flask(__name__)
CORS(app)

# --- ▼▼▼【修正点】Excelファイルをローカルではなく、GitHubの公開URLから直接読み込む ▼▼▼ ---
# これにより、Vercelのデプロイサイズ制限とファイル形式エラーを回避します。
chart_file_url = 'https://raw.githubusercontent.com/oganes-son/random_aochart/main/aochart.xlsx'
ex_file_url = 'https://raw.githubusercontent.com/oganes-son/random_aochart/main/aochart_ex.xlsx'

df_chart = None
df_ex = None
column_mapping = {
    1: 'unit_name', 2: 'difficulty', 3: 'problem_number', 4: 'problem_text', 
    5: 'image_flag', 6: 'image_number'
}

try:
    df_chart = pd.read_excel(chart_file_url, dtype=str, header=None, engine='openpyxl')
    df_chart = df_chart.rename(columns=column_mapping)
    print("Chart Excel file loaded successfully from URL.")
except Exception as e:
    print(f"Failed to load Chart Excel from URL: {e}")

try:
    df_ex = pd.read_excel(ex_file_url, dtype=str, header=None, engine='openpyxl')
    df_ex = df_ex.rename(columns=column_mapping)
    print("Exercise Excel file loaded successfully from URL.")
except Exception as e:
    print(f"Failed to load Exercise Excel from URL: {e}")
# --- ▲▲▲ 修正ここまで ▲▲▲ ---


def process_latex_text(problem_text):
    """
    ラッピング済みのテキストに対して、最終的な微調整と、
    過去に見つかった特定のデータエラーの修復のみを行う。
    """
    if not isinstance(problem_text, str): return ""
    
    # ドル記号のデリミタをバックスラッシュ形式に統一
    text = re.sub(r'\$\$(.*?)\$\$', r'\\\[\1\\\]', problem_text, flags=re.DOTALL)
    text = re.sub(r'\$([^$]*?)\$', r'\\(\1\\)', text)
    
    # 二重ラップを解消
    while r'\(\(' in text: text = text.replace(r'\(\(', r'\(')
    while r'\)\)' in text: text = text.replace(r'\)\)', r'\)')

    # デリミタ周りの一貫しないスペースを正規化（削除）
    text = text.replace(r'\ (', r'\(').replace(r'\ )', r'\)').replace(r'\ [', r'\[').replace(r'\ ]', r'\]')

    # 読点とカンマの処理
    text = text.replace('、', ',')
    text = re.sub(r',(?!\s)', r', ', text)

    # データソース内の特定の記述ミスを修正
    text = text.replace('＾', '^').replace(r'\left\)', r'\left(').replace(r'\right\(', r'\right)')
    text = re.sub(r'f\\\)\s*\((\d+)\)\\\(', r'f(\1)', text)
    
    # 数式デリミタの前後に必要に応じてスペースを挿入
    text = re.sub(r'(?<!\s)(\\[\(\[])', r' \1', text)
    text = re.sub(r'(\\[\)\]])(?!\s)', r'\1 ', text)
    
    return text

class ProblemFormatter:
    """
    問題文をHTML形式に整形するクラス。
    """
    def __init__(self):
        self.item_pattern = re.compile(
            r'(?<![a-zA-Z_0-9\(])'
            r'('
            r'([①-⑳])|(\((?:[1-9]|1[0-9]|20)\)(?!の|は|が|で|と|より|から|の値))|(\([ア-コ]\))'
            r')'
        )
        self.math_pattern = re.compile(r'(\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\]|\$\$.*?\$\$)', re.DOTALL)
        self.series_types_found = []
    def _replacer(self, match):
        full_match = match.group(1)
        current_series_type = None
        if match.group(2): current_series_type = 'round_num'
        elif match.group(3): current_series_type = 'paren_num'
        elif match.group(4): current_series_type = 'paren_kana'
        if current_series_type and current_series_type not in self.series_types_found:
            self.series_types_found.append(current_series_type)
        indent = ''
        if current_series_type and self.series_types_found.index(current_series_type) >= 1: indent = '&emsp;'
        return f"</p><p>{indent}{full_match}"
    def _format_text_part(self, text_part):
        return self.item_pattern.sub(self._replacer, text_part)
    def _format_fractions(self, math_part):
        delimiters = None
        if math_part.startswith(r'\[') and math_part.endswith(r'\]'): delimiters = (r'\[', r'\]')
        elif math_part.startswith(r'\(') and math_part.endswith(r'\)'): delimiters = (r'\(', r'\)')
        elif math_part.startswith('$$') and math_part.endswith('$$'): delimiters = ('$$', '$$')
        elif math_part.startswith('$') and math_part.endswith('$'): delimiters = ('$', '$')
        else: return math_part
        content = math_part[len(delimiters[0]):-len(delimiters[1])]
        output_str, i, brace_level = "", 0, 0
        while i < len(content):
            if content[i:i+5] == '\\frac':
                if brace_level == 0: output_str += '\\dfrac'
                else: output_str += '\\frac'
                i += 5
            elif content[i] == '{':
                if i == 0 or content[i-1] != '\\': brace_level += 1
                output_str += content[i]; i += 1
            elif content[i] == '}':
                if i == 0 or content[i-1] != '\\': brace_level = max(0, brace_level - 1)
                output_str += content[i]; i += 1
            else: output_str += content[i]; i += 1
        return delimiters[0] + output_str + delimiters[1]
    def format(self, text):
        if not isinstance(text, str) or not text.strip(): return ""
        self.series_types_found = []
        parts = self.math_pattern.split(text)
        formatted_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0: formatted_parts.append(self._format_text_part(part))
            else: formatted_parts.append(self._format_fractions(part))
        formatted_text = "".join(formatted_parts)
        final_html = f"<p>{formatted_text}</p>"
        if final_html.startswith("<p></p>"): final_html = final_html[len("<p></p>"):]
        final_html = re.sub(r'(<p>\s*</p>)+', '', final_html)
        return final_html

problem_formatter = ProblemFormatter()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_problem', methods=['POST'])
def get_problem():
    try:
        if not request.is_json: return jsonify(error="リクエストの形式が不正です。"), 400
        data = request.get_json()
        if not data: return jsonify(error="リクエストボディが空です。"), 400
        selected_book = data.get('book', 'all')
        selected_units = data.get('units', [])
        raw_difficulties = data.get('difficulties', [])
        selected_difficulties = [int(d) for d in raw_difficulties if isinstance(d, (int, str)) and str(d).isdigit()]
        if not selected_units or not selected_difficulties: return jsonify(error="単元と難易度を少なくとも1つずつ選択してください。")
        df_list = []
        if selected_book in ['all', 'chart'] and df_chart is not None:
            temp_chart = df_chart.copy(); temp_chart['source'] = 'chart'; df_list.append(temp_chart)
        if selected_book in ['all', 'ex'] and df_ex is not None:
            temp_ex = df_ex.copy(); temp_ex['source'] = 'ex'; df_list.append(temp_ex)
        if not df_list: return jsonify(error="選択可能な問題集のデータが見つかりません。")
        target_df = pd.concat(df_list, ignore_index=True)
        target_df['difficulty'] = pd.to_numeric(target_df['difficulty'], errors='coerce').fillna(0).astype(int)
        matching_rows = target_df[(target_df['unit_name'].isin(selected_units)) & (target_df['difficulty'].isin(selected_difficulties))]
        if matching_rows.empty: return jsonify(error="選択した単元と難易度に合致する問題が見つかりません。")
        random_row = matching_rows.sample(n=1).iloc[0]
        unit_name, example_number = random_row['unit_name'], random_row['problem_number']
        problem_number_display = f"EXERCISE {example_number}" if 'source' in random_row and random_row['source'] == 'ex' else str(example_number)
        raw_problem_text = process_latex_text(random_row['problem_text'])
        formatted_equation = problem_formatter.format(raw_problem_text)
        image_flag = int(random_row['image_flag']) if pd.notna(random_row['image_flag']) else 0
        image_number = int(random_row['image_number']) if pd.notna(random_row['image_number']) else None
        difficulty = int(random_row['difficulty']) if pd.notna(random_row['difficulty']) else 0
        return jsonify(unit_name=unit_name, problem_number=problem_number_display, equation=formatted_equation, image_flag=image_flag, image_number=image_number, difficulty=difficulty)
    except Exception as e:
        app.logger.error(f"Error in /get_problem: {e}\n{traceback.format_exc()}"); return jsonify(error="サーバー側で予期せぬエラーが発生しました。", details=str(e)), 500

@app.route('/get_selected_problem')
def get_selected_problem():
    try:
        book_type = request.args.get('book', 'chart')
        selected_unit, problem_number = request.args.get('unit'), request.args.get('problem_number')
        target_df = df_ex if book_type == 'ex' else df_chart
        if target_df is None: return jsonify(error=f"問題データ({book_type})が読み込まれていません。")
        if not selected_unit or not problem_number: return jsonify(error="単元と問題番号が指定されていません。")
        target_df['problem_number'] = target_df['problem_number'].astype(str)
        row = target_df[(target_df['unit_name'] == selected_unit) & (target_df['problem_number'] == str(problem_number))]
        if row.empty: return jsonify(error=f"問題が見つかりません: {selected_unit} - {problem_number}")
        row = row.iloc[0]
        raw_latex_data = process_latex_text(row['problem_text'])
        formatted_equation = problem_formatter.format(raw_latex_data)
        image_flag = int(row['image_flag']) if pd.notna(row['image_flag']) else 0
        image_number = int(row['image_number']) if pd.notna(row['image_number']) else None
        difficulty = int(row['difficulty']) if pd.notna(row['difficulty']) else 0
        return jsonify(problem_number=problem_number, equation=formatted_equation, difficulty=difficulty, image_flag=image_flag, image_number=image_number, row_number=int(row.name))
    except Exception as e:
        app.logger.error(f"Error in /get_selected_problem: {e}\n{traceback.format_exc()}"); return jsonify(error="サーバー側で予期せぬエラーが発生しました。", details=str(e)), 500

# ローカルテスト用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
