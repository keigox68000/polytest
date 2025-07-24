// このコードは、生成されたHTMLファイルの </body> タグの直前に貼り付けます。
const canvas = document.querySelector('canvas');

// ドラッグ中の見た目を変更
window.addEventListener('dragover', (event) => {
    event.preventDefault();
    canvas.style.border = '2px dashed #00ff00';
});

window.addEventListener('dragleave', (event) => {
    event.preventDefault();
    canvas.style.border = 'none';
});

// ファイルがドロップされたときの処理
window.addEventListener('drop', (event) => {
    event.preventDefault();
    canvas.style.border = 'none';

    if (event.dataTransfer.items) {
        if (event.dataTransfer.items[0].kind === 'file') {
            const file = event.dataTransfer.items[0].getAsFile();
            
            // ファイルが.wrlかどうかを簡易的にチェック
            if (file.name.toLowerCase().endsWith('.wrl')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const wrlContent = e.target.result;
                    // Pythonの load_wrl_data 関数を呼び出す
                    if (window.pyodide && pyodide.globals.has('load_wrl_data')) {
                        pyodide.globals.get('load_wrl_data')(wrlContent);
                    } else {
                        console.error("Pyodide or 'load_wrl_data' function not found.");
                    }
                };
                reader.readAsText(file);
            } else {
                console.log('Please drop a .wrl file.');
            }
        }
    }
});
