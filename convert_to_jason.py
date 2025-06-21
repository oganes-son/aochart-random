import pandas as pd
import json
import os
import traceback

# --- 設定 ---
# 変換元のExcelファイルと、出力先のJSONファイル名を指定
excel_files_to_convert = {
    'aochart.xlsx': 'aochart.json',
    'aochart_ex.xlsx': 'aochart_ex.json'
}

# Excelの列番号とプログラムで使う名前の対応表
column_mapping = {
    1: 'unit_name', 2: 'difficulty', 3: 'problem_number', 4: 'problem_text', 
    5: 'image_flag', 6: 'image_number'
}

# --- 処理 ---
for excel_file, json_file in excel_files_to_convert.items():
    if not os.path.exists(excel_file):
        print(f"ファイルが見つかりません: {excel_file}。スキップします。")
        continue

    try:
        print(f"{excel_file} を読み込んでいます...")
        # header=Noneでヘッダーなしとして読み込む
        df = pd.read_excel(excel_file, dtype=str, header=None)
        
        # 必要な列だけを抽出
        df = df[list(column_mapping.keys())]
        # 列名を変更
        df = df.rename(columns=column_mapping)
        
        # DataFrameをJSON形式（レコード指向）のリストに変換
        records = df.to_dict('records')
        
        # JSONファイルとして保存 (UTF-8で)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
            
        print(f"正常に {json_file} を作成しました。")

    except Exception as e:
        print(f"{excel_file} の処理中にエラーが発生しました: {e}")
        traceback.print_exc()

print("\nすべての処理が完了しました。プロジェクトフォルダに2つのJSONファイルが作成されたことを確認してください。")
