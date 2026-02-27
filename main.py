import discord
from discord.ext import commands
import os
from flask import Flask, request, jsonify
from threading import Thread

# Configuração do Flask (Para o seu Site e UptimeRobot)
app = Flask('')

@app.route('/')
def home():
    return "Servidor do Bot está Vivo!"

# Rota para o seu site enviar o código fonte via POST
@app.route('/update_code', methods=['POST'])
def update_code():
    data = request.json
    novo_codigo = data.get('code')
    with open("bot_logic.py", "w") as f:
        f.write(novo_codigo)
    return jsonify({"message": "Código atualizado! Reinicie o bot."})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Configuração do Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot logado como {bot.user}')

# Início de tudo
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Aguardando Token via variável de ambiente no Render...")

        
