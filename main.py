import os
import subprocess
import signal
import time
import requests
import discord
import asyncio
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)
bot_process = None 

# --- SITE HTML COM VERIFICAÇÃO DE TOKEN ---
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
        textarea { width: 100%; height: 200px; background: #000; color: #0f0; border: 1px solid #333; padding: 15px; border-radius: 8px; font-family: monospace; margin-bottom: 20px; outline: none; }
        input { width: 100%; padding: 12px; background: #000; border: 1px solid #333; color: #fff; border-radius: 8px; margin-bottom: 20px; box-sizing: border-box; }
        .btn { width: 100%; background: var(--primary); color: white; border: none; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn:hover { background: #cc0000; }
        #log { margin-top: 20px; font-size: 14px; padding: 10px; border-radius: 5px; display: none; }
        .error { background: rgba(255,0,0,0.1); color: #ff4d4d; border: 1px solid #ff0000; }
        .success { background: rgba(0,255,0,0.1); color: #00ff00; border: 1px solid #00ff00; }
    </style>
</head>
<body>
    <div class="box">
        <h1><i class="fas fa-shield-virus"></i> XSSX Verificador</h1>
        <input type="password" id="token" placeholder="Insira o Token do Bot aqui para verificar">
        <textarea id="code" placeholder="Insira o código Python do bot aqui..."></textarea>
        <button class="btn" onclick="verificarELigar()">VERIFICAR E LIGAR</button>
        <div id="log"></div>
    </div>
    <script>
        async function verificarELigar() {
            const token = document.getElementById('token').value;
            const code = document.getElementById('code').value;
            const log = document.getElementById('log');
            
            if(!token || !code) return alert("Preencha o Token e o Código!");

            log.style.display = "block";
            log.className = "status";
            log.style.color = "#aaa";
            log.innerHTML = "⏳ Validando Token com o Discord...";

            try {
                const res = await fetch('/hospedar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code, token: token })
                });
                const data = await res.json();
                
                if(data.status === 'sucesso') {
                    log.className = "success";
                    log.innerHTML = `✅ <b>Bot Identificado!</b><br>Nome: ${data.bot_name}<br>User: @${data.bot_user}<br><br>🚀 Instância iniciada com sucesso!`;
                } else {
                    log.className = "error";
                    log.innerHTML = `❌ <b>Erro:</b> ${data.msg}`;
                }
            } catch(e) { 
                log.className = "error";
                log.innerHTML = "❌ Falha ao conectar ao servidor."; 
            }
        }
    </script>
</body>
</html>
"""

async def validate_token(token):
    """Tenta conectar ao Discord apenas para pegar o nome do bot"""
    client = discord.Client(intents=discord.Intents.none())
    try:
        await client.login(token)
        info = {"name": client.user.name, "user": str(client.user)}
        await client.close()
        return info
    except:
        return None

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    codigo = data.get('code')
    token = data.get('token')

    # 1. Verificar se o Token é válido antes de tudo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot_info = loop.run_until_complete(validate_token(token))
    
    if not bot_info:
        return jsonify({"status": "erro", "msg": "Token Inválido ou Sem Conexão!"}), 400

    # 2. Encerrar bot anterior
    if bot_process:
        try: os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except: pass

    # 3. Salva e executa o bot cliente
    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        # Injeta o token automaticamente no final do código enviado
        f.write(f"{codigo}\n\nbot.run('{token}')")

    try:
        bot_process = subprocess.Popen(["python", "bot_cliente.py"], preexec_fn=os.setsid)
        return jsonify({
            "status": "sucesso", 
            "bot_name": bot_info['name'], 
            "bot_user": bot_info['user']
        })
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

def self_ping():
    while True:
        try: requests.get("https://ticket-xssx.onrender.com")
        except: pass
        time.sleep(600)

if __name__ == "__main__":
    Thread(target=self_ping, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
