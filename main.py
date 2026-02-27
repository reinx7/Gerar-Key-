import os, subprocess, signal, time, requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)
bot_process = None 

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8"><title>XSSX DEBUGGER</title>
    <style>
        body { background: #080808; color: white; font-family: sans-serif; text-align: center; padding: 50px; }
        .box { background: #111; padding: 20px; border-radius: 10px; border: 1px solid #ff0000; display: inline-block; width: 90%; max-width: 500px; }
        input, textarea { width: 100%; margin: 10px 0; padding: 10px; background: #000; color: #0f0; border: 1px solid #333; }
        button { width: 100%; padding: 15px; background: #ff0000; color: white; border: none; cursor: pointer; font-weight: bold; }
        #log { margin-top: 20px; padding: 10px; background: #222; border-radius: 5px; font-family: monospace; font-size: 12px; text-align: left; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="box">
        <h1>XSSX HOST DEBUG</h1>
        <input type="password" id="token" placeholder="TOKEN DO DISCORD">
        <textarea id="code" placeholder="CÓDIGO DO BOT" rows="10"></textarea>
        <button onclick="ligar()">LIGAR E VER LOGS</button>
        <div id="log">Aguardando início...</div>
    </div>
    <script>
        async function ligar() {
            const log = document.getElementById('log');
            log.innerHTML = "⏳ Iniciando e capturando logs...";
            const res = await fetch('/hospedar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    code: document.getElementById('code').value,
                    token: document.getElementById('token').value
                })
            });
            const data = await res.json();
            if(data.status === 'sucesso') {
                log.innerHTML = "🚀 Comando enviado! Verificando saída do console...\\n";
                checarLogs();
            }
        }

        async function checarLogs() {
            const res = await fetch('/get_logs');
            const data = await res.json();
            document.getElementById('log').innerHTML = data.logs || "Sem logs ainda...";
            setTimeout(checarLogs, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_PAGE)

@app.route('/get_logs')
def get_logs():
    if os.path.exists("bot.log"):
        with open("bot.log", "r") as f: return jsonify({"logs": f.read()})
    return jsonify({"logs": "Iniciando..."})

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    if bot_process:
        try: os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except: pass
    
    with open("bot_cliente.py", "w") as f:
        f.write(f"{data['code']}\\n\\nbot.run('{data['token']}')")
    
    # Abre o bot e joga os erros num arquivo de texto para o site ler
    with open("bot.log", "w") as log_file:
        bot_process = subprocess.Popen(["python", "-u", "bot_cliente.py"], 
                                     stdout=log_file, stderr=log_file, preexec_fn=os.setsid)
    
    return jsonify({"status": "sucesso"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 8080))
