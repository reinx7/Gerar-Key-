import os
import subprocess
import signal
import time
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from threading import Thread

# Configuração do Aplicativo
app = Flask(__name__)
CORS(app)
bot_process = None 

# --- DESIGN DO PAINEL (VERMELHO XSSX) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XSSX CORE | PRODUCTION</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --bg: #080808; --red: #ff0000; --card: #111; }
        body { background: var(--bg); color: #eee; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: var(--card); padding: 35px; border-radius: 12px; border: 1px solid #222; width: 90%; max-width: 550px; box-shadow: 0 0 30px rgba(255,0,0,0.15); }
        h1 { color: var(--red); font-size: 22px; text-transform: uppercase; text-align: center; letter-spacing: 2px; }
        input, textarea { width: 100%; background: #000; border: 1px solid #333; color: #fff; border-radius: 6px; padding: 12px; margin-bottom: 15px; box-sizing: border-box; font-family: monospace; outline: none; }
        input:focus, textarea:focus { border-color: var(--red); }
        .btn { width: 100%; background: var(--red); color: #fff; border: none; padding: 15px; border-radius: 6px; font-weight: bold; cursor: pointer; text-transform: uppercase; transition: 0.3s; }
        .btn:hover { background: #b30000; box-shadow: 0 0 15px rgba(255,0,0,0.4); }
        #status { margin-top: 15px; padding: 12px; border-radius: 6px; display: none; text-align: center; font-size: 14px; font-weight: bold; }
        .info { background: rgba(255,255,255,0.05); color: #bbb; }
        .success { background: rgba(0,255,0,0.1); color: #00ff00; border: 1px solid #00ff00; }
        .error { background: rgba(255,0,0,0.1); color: #ff3333; border: 1px solid #ff3333; }
    </style>
</head>
<body>
    <div class="box">
        <h1><i class="fas fa-terminal"></i> XSSX Cloud Engine</h1>
        <p style="text-align:center; font-size:11px; color:#555; margin-bottom:20px;">Ambiente de Produção Gunicorn Ativo</p>
        
        <input type="password" id="token" placeholder="COLE O TOKEN DO BOT AQUI">
        <textarea id="code" placeholder="COLE O CÓDIGO DO BOT (O que te mandei antes)"></textarea>
        
        <button class="btn" onclick="iniciarInstancia()">Ligar Instância</button>
        <div id="status"></div>
    </div>

    <script>
        async function iniciarInstancia() {
            const token = document.getElementById('token').value;
            const code = document.getElementById('code').value;
            const status = document.getElementById('status');
            
            if(!token || !code) return alert("Preencha o Token e o Código!");

            status.style.display = "block";
            status.className = "info";
            status.innerHTML = "⏳ Enviando requisição para os workers...";

            try {
                const res = await fetch('/hospedar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code, token: token })
                });
                const data = await res.json();
                
                if(data.status === 'sucesso') {
                    status.className = "success";
                    status.innerHTML = "🚀 INSTÂNCIA INICIADA! Verifique o Discord em 10 segundos.";
                } else {
                    status.className = "error";
                    status.innerHTML = "❌ ERRO: " + data.msg;
                }
            } catch(e) {
                status.className = "error";
                status.innerHTML = "❌ FALHA NA COMUNICAÇÃO COM O CORE";
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
    token = data.get('token')

    if not token or not codigo:
        return jsonify({"status": "erro", "msg": "Dados incompletos!"}), 400

    # 1. Mata o processo anterior (Bot antigo)
    if bot_process:
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except:
            pass

    # 2. Escreve o arquivo final do bot injetando o Token
    # Adicionamos um print para você ver o que acontece nos logs do Render
    script_final = f"""
import discord
from discord.ext import commands
import sys

print("--- INICIANDO BOT CLIENTE ---")
{codigo}

if 'bot' in locals():
    try:
        bot.run('{token}')
    except Exception as e:
        print(f'ERRO NO LOGIN: {{e}}', file=sys.stderr)
else:
    print("ERRO: A variável 'bot' não foi definida no seu código!", file=sys.stderr)
"""

    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(script_final)

    try:
        # 3. Executa o bot como um processo filho independente
        bot_process = subprocess.Popen(
            ["python", "bot_cliente.py"],
            preexec_fn=os.setsid
        )
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

# --- SISTEMA DE MANUTENÇÃO (KEEP-ALIVE) ---
def self_ping():
    """Mantém o Render acordado"""
    time.sleep(10) # Espera o servidor subir
    while True:
        try:
            # Tenta acessar o próprio site
            requests.get("http://localhost:8080")
        except:
            pass
        time.sleep(600) # a cada 10 minutos

# Inicia a thread de manutenção apenas uma vez
Thread(target=self_ping, daemon=True).start()

# O Gunicorn usará o objeto 'app' definido acima.
# O bloco abaixo só roda se você usar 'python main.py' localmente.
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
