import os
import subprocess
import signal
import time
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)
bot_process = None 

# --- SITE HTML COM DESIGN VERMELHO ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XSSX HOST | CORE</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --bg: #0a0a0a; --primary: #ff0000; --card: #121212; }
        body { background: var(--bg); color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: var(--card); padding: 40px; border-radius: 15px; border: 1px solid #222; width: 90%; max-width: 600px; text-align: center; box-shadow: 0 0 20px rgba(255,0,0,0.1); }
        h1 { color: var(--primary); font-size: 24px; text-transform: uppercase; margin-bottom: 20px; }
        textarea { width: 100%; height: 250px; background: #000; color: #0f0; border: 1px solid #333; padding: 15px; border-radius: 8px; font-family: monospace; margin-bottom: 20px; outline: none; }
        .btn { width: 100%; background: var(--primary); color: white; border: none; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn:hover { background: #cc0000; transform: scale(1.02); }
        #log { margin-top: 20px; font-size: 14px; color: #888; }
    </style>
</head>
<body>
    <div class="box">
        <h1><i class="fas fa-microchip"></i> XSSX Cloud Core</h1>
        <textarea id="code" placeholder="Insira o código do bot aqui..."></textarea>
        <button class="btn" onclick="ligar()">LIGAR INSTÂNCIA</button>
        <div id="log">Aguardando comando...</div>
    </div>
    <script>
        async function ligar() {
            const code = document.getElementById('code').value;
            const log = document.getElementById('log');
            log.innerHTML = "⏳ Iniciando processo...";
            try {
                const res = await fetch('/hospedar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code })
                });
                const data = await res.json();
                if(data.status === 'sucesso') log.innerHTML = "<b style='color:#0f0'>✅ BOT ENVIADO!</b> Verifique o Discord.";
            } catch(e) { log.innerHTML = "<b style='color:#f00'>❌ Erro de conexão.</b>"; }
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

    # Encerrar bot anterior de forma limpa
    if bot_process:
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except:
            pass

    # Salva o bot em um arquivo
    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(codigo)

    try:
        # Inicia o bot em um novo grupo de processos
        bot_process = subprocess.Popen(
            ["python", "bot_cliente.py"],
            preexec_fn=os.setsid
        )
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

# --- FUNÇÃO KEEP ALIVE (O "PULO DO GATO") ---
def self_ping():
    """Faz o servidor visitar a si mesmo a cada 10 minutos para não dormir"""
    while True:
        try:
            # Substitua pelo seu link real do Render
            requests.get("https://ticket-xssx.onrender.com")
            print("🚀 Auto-ping realizado com sucesso!")
        except:
            print("❌ Falha no auto-ping.")
        time.sleep(600) # 10 minutos

if __name__ == "__main__":
    # Inicia a thread de auto-visita
    t = Thread(target=self_ping)
    t.daemon = True
    t.start()
    
    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=8080)
