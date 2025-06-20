document.addEventListener("DOMContentLoaded", function() {
    // MathJaxの初期化
    if (typeof MathJax !== "undefined" && MathJax.typesetPromise) {
      MathJax.typesetPromise();
    }

    // --- 履歴機能のためのグローバル変数 ---
    let problemHistory = []; 

    // --- パスワードチェック (変更なし) ---
    window.checkPassword = function() {
      const inputPassword = document.getElementById("password").value;
      if (inputPassword === "sugaku") {
        document.getElementById("login").style.display = "none";
        document.getElementById("content").style.display = "block";
      } else {
        alert("パスワードが間違っています");
      }
    }
  
    // --- 難易度テキスト生成ヘルパー関数 ---
    function getDifficultyText(level) {
        const descriptions = {
            1: '（教科書の例レベル）',
            2: '（教科書の例題レベル）',
            3: '（教科書の節末・章末レベル）',
            4: '（入試の基本～標準レベル）',
            5: '（入試の標準～やや難レベル）'
        };
        const stars = "★".repeat(level) + "☆".repeat(5 - level);
        return `${stars} ${descriptions[level] || ''}`;
    }

    // --- 受け取った問題データを表示する共通関数 ---
    function displayProblem(data, fromHistory = false) {
        if (!data) return;
        document.getElementById("unit_name").innerText = data.unit_name || '';
        document.getElementById("problem_number").innerText = data.problem_number || '';
        const difficulty = parseInt(data.difficulty, 10);
        document.getElementById("difficulty_level").innerText = getDifficultyText(difficulty);
        const equationContainer = document.getElementById("equation_container");
        equationContainer.innerHTML = data.equation || '';
        MathJax.typesetPromise([equationContainer]);
        if (!fromHistory) {
            problemHistory.push(data);
            renderHistoryTable();
        }
    }
  
    // --- ランダムモードで問題を取得 ---
    window.getProblem = function() {
      const selectedBook = document.querySelector('input[name="book_select"]:checked').value;
      const selectedUnits = Array.from(document.querySelectorAll(".unit-checkbox:checked")).map(cb => cb.dataset.value).filter(Boolean);
      const selectedDifficulties = Array.from(document.querySelectorAll("#difficult .unit-checkbox:checked")).map(cb => cb.dataset.difficulty).filter(Boolean);
  
      if (selectedUnits.length === 0) {
        document.getElementById("error-message").style.display = "block";
        return;
      } else {
        document.getElementById("error-message").style.display = "none";
      }
  
      fetch("/get_problem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ book: selectedBook, units: selectedUnits, difficulties: selectedDifficulties }),
      })
        .then(response => { if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`); return response.json(); })
        .then(data => {
            if (data.error) { alert(data.error); return; }
            displayProblem(data, false);
        })
        .catch(error => { console.error("問題の取得中にエラーが発生しました:", error); alert("問題の取得中にエラーが発生しました。コンソールを確認してください。"); });
    }

    // --- 履歴関連の関数群 ---
    function renderHistoryTable() {
        const tbody = document.getElementById('history_table_body');
        tbody.innerHTML = ''; 
        [...problemHistory].reverse().forEach((problem, index) => {
            const originalIndex = problemHistory.length - 1 - index;
            const row = tbody.insertRow();
            row.dataset.historyIndex = originalIndex;
            const originalHTML = (problem.equation || '').replace(/<p>|<\/p>/g, ' ').trim();
            let previewHTML = originalHTML;
            if (originalHTML.length > 30) {
                let cutPoint = 30;
                let firstSpace = originalHTML.indexOf(' ', cutPoint);
                if(firstSpace > -1) { cutPoint = firstSpace; }
                const substring = originalHTML.substring(0, cutPoint);
                const openDelimiters = (substring.match(/\\\(/g) || []).length;
                const closeDelimiters = (substring.match(/\\\)/g) || []).length;
                if (openDelimiters > closeDelimiters) {
                    const endOfMath = originalHTML.indexOf('\\)', cutPoint);
                    if (endOfMath > -1) { previewHTML = originalHTML.substring(0, endOfMath + 2); } 
                    else { previewHTML = originalHTML.replace(/\\\(|\\\)|\\\[|\\\]|\$|\$\$/g, '').substring(0, 30); }
                } else { previewHTML = substring; }
                previewHTML += '...';
            }
            row.insertCell(0).innerText = originalIndex + 1;
            row.insertCell(1).innerText = problem.problem_number;
            const previewCell = row.insertCell(2);
            previewCell.innerHTML = previewHTML;
        });
        MathJax.typesetPromise([tbody]);
    }

    document.getElementById('history_table_body').addEventListener('click', function(event) {
        const row = event.target.closest('tr');
        if (row && row.dataset.historyIndex) {
            const index = parseInt(row.dataset.historyIndex, 10);
            displayProblem(problemHistory[index], true);
        }
    });

    window.toggleHistory = function() {
        const historySection = document.getElementById('history_section');
        const button = document.getElementById('toggle_history_button');
        const isHidden = historySection.style.display === 'none';
        if (isHidden) {
            historySection.style.display = 'block';
            button.innerText = '履歴を非表示';
        } else {
            historySection.style.display = 'none';
            button.innerText = '履歴を表示';
        }
    }
  
    // --- 選択モードの処理 ---
    window.getSelectedProblem = function() {
      const selectedBook = document.getElementById('select_book_type').value;
      const unitSelect = document.getElementById(selectedBook === 'chart' ? 'unit_select_chart' : 'unit_select_ex');
      const unit = unitSelect.value;
      const problemNumber = document.getElementById("problem_number_input").value;
      
      fetch(`/get_selected_problem?book=${selectedBook}&unit=${encodeURIComponent(unit)}&problem_number=${encodeURIComponent(problemNumber)}`)
        .then(response => { if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`); return response.json(); })
        .then(data => {
          if (data.error) { alert(data.error); return; }
          document.getElementById("selected_problem_number").innerText = data.problem_number;
          const difficulty = parseInt(data.difficulty, 10);
          document.getElementById("selected_difficulty_display").innerText = getDifficultyText(difficulty);
          const selectedEquationContainer = document.getElementById("selected_equation_container");
          selectedEquationContainer.innerHTML = data.equation;
          MathJax.typesetPromise([selectedEquationContainer]);
        })
        .catch(error => { console.error("問題の取得中にエラーが発生しました:", error); alert("問題の取得中にエラーが発生しました。コンソールを確認してください。"); });
    }

    // 選択モードの問題集ドロップダウンのイベントリスナー
    document.getElementById('select_book_type').addEventListener('change', function() {
        const chartSelect = document.getElementById('unit_select_chart');
        const exSelect = document.getElementById('unit_select_ex');
        if (this.value === 'chart') {
            chartSelect.style.display = 'block';
            exSelect.style.display = 'none';
        } else {
            chartSelect.style.display = 'none';
            exSelect.style.display = 'block';
        }
    });
  
    // --- 以下、変更なし ---
    window.toggleProblemDetails = function() {
      const details = document.getElementById("problem_details");
      const button = document.getElementById("toggle_details");
      const isHidden = details.style.display === "none" || details.style.display === "";
      if (isHidden) { details.style.display = "block"; button.innerText = "問題の詳細を非表示"; } 
      else { details.style.display = "none"; button.innerText = "問題の詳細を表示"; }
    }
  
    document.querySelectorAll(".unit-toggle").forEach(function(toggle) {
      toggle.addEventListener("change", function() {
        const targetId = this.dataset.target;
        const checkboxes = document.querySelectorAll(`#${targetId} .unit-checkbox`);
        checkboxes.forEach(function(checkbox) { checkbox.checked = toggle.checked; });
      });
    });
  
    document.querySelectorAll(".accordion .title").forEach(function(title) {
      title.addEventListener("click", function(event) {
        if (event.target.closest('.toggle-switch')) return;
        const content = this.nextElementSibling;
        const arrowIcon = this.querySelector(".fa-angle-down");
        if (content.style.maxHeight) { content.style.maxHeight = null; } 
        else { content.style.maxHeight = content.scrollHeight + "px"; }
        content.classList.toggle("content-open");
        if (arrowIcon) arrowIcon.classList.toggle("fa-rotate-180");
      });
    });
});
