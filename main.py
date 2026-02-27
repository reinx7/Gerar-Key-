import os
import subprocess
import signal
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# --- CONFIGURAÇÃO DO BOT PAI ---
intents = discord.Intents.default()
intents.message_content = True
bot_pai = commands.Bot(command_prefix="!", intents=intents)

@bot_pai.event
async def on_ready():
    print(f'✅ Bot Pai {bot_pai.user} está online!')
    await bot_pai.tree.sync()

# --- CONFIGURAÇÃO DO SERVIDOR WEB ---
app = Flask(__name__)
CORS(app)
bot_process = None 

@app.route('/')
def index():
    return "Servidor XSSX Online!"

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    token = data.get('token')
    codigo = data.get('code')

    if bot_process:
        try: os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except: pass

    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(f"{codigo}\n\nbot.run('{token}')")

    try:
        bot_process = subprocess.Popen(["python", "bot_cliente.py"], preexec_fn=os.setsid)
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    # Liga o Flask
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Liga o Bot
    token_principal = os.environ.get('DISCORD_TOKEN')
    if token_principal:
        bot_pai.run(token_principal)
    else:
        print("Erro: Falta o DISCORD_TOKEN nas variáveis do Render!")
        while True: pass
            
