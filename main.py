import os
import subprocess
import signal
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)
bot_process = None 

# --- O SITE HTML INTEGRADO ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XSSX HOST | Painel Oficial</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --bg: #0d0d0d; --card: #161616; --primary: #ff1a1a; --text: #e0e0e0; }
        body { background: var(--bg); color: var(--text); font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: var(--card); width: 90%; max-width: 700px; padding: 30px; border-radius: 15px; border: 1px solid #333; box-shadow: 0 0 20px rgba(255, 26, 26, 0.2); }
        h1 { color: var(--primary); text-align: center; text-transform: uppercase; }
        textarea { width: 100%; height: 300px; background: #000; color: #0f0; border: 1px solid #444; padding: 15px; border-radius: 8px; font-family: monospace; box-sizing: border-box; }
        .btn { width: 100%; background: var(--primary); color: #fff; border: none; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 20px; font-size: 16px; }
        .status { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; text-align: center; }
        .loading { background: rgba(255, 26, 26, 0.1); color: var(--primary); }
        .success { background: rgba(0, 255, 0, 0.1); color: #00ff00; }
    </style>
</head>
<body>
    <div class="card">
        <h1><i class="fas fa-rocket"></i> XSSX CLOUD</h1>
        <p style="text-align:center">Cole seu código completo abaixo:</p>
        <textarea id="code" placeholder="import discord..."></textarea>
        <button class="btn" onclick="hospedar()">INICIAR BOT</button>
        <div id="status" class="status"></div>
    </div>

    <script>
        async function hospedar() {
            const code = document.getElementById('code').value;
            const status = document.getElementById('status');
            if(!code) return alert("Cole o código!");

            status.style.display = "block";
            status.className = "status loading";
            status.innerHTML = "🚀 Enviando código para o núcleo...";

            try {
                const res = await fetch('/hospedar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code })
                });
                const data = await res.json();
                if(data.status === "sucesso") {
                    status.className = "status success";
                    status.innerHTML = "✅ BOT ONLINE! Verifique seu Discord.";
                }
            } catch (e) {
                status.innerHTML = "❌ Erro ao conectar.";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    codigo = data.get('code')

    if bot_process:
        try: os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except: pass

    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(codigo)

    try:
        bot_process = subprocess.Popen(["python", "bot_cliente.py"], preexec_fn=os.setsid)
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
