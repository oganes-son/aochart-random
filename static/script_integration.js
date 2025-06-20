// script_integration.js

document.addEventListener("DOMContentLoaded", function() {
    // 例えば、問題選択ボタンに対してクリックイベントを設定する
    const getProblemButton = document.getElementById("get_problem_button");
    if(getProblemButton) {
      getProblemButton.addEventListener("click", function() {
        // ここでは、すでに script.js に定義した getProblem() を呼び出す想定です
        // getProblem() 内で fetch したデータを処理し、equation_container に反映し、MathJax.typesetPromise() を呼んでいる場合、
        // そのまま呼び出すこともできます。
        getProblem(); // getProblem() は script.js で定義済み
      });
    }
  
    // あるいは、ページ読み込み時に初期データを取得して表示する例
    const initProblem = function() {
      // getProblem() を呼び出し、問題文を表示、MathJax を再レンダリングする
      getProblem();
    };
  
    // 必要に応じて初期化処理を呼び出す
    initProblem();
  });
  