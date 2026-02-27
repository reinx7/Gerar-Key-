import os
import subprocess
import signal
import discord
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)
bot_process = None 

@app.route('/')
def index():
    return "<h1>XSSX HOST ATIVO</h1><p>Aguardando comando do painel...</p>"

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    codigo_bruto = data.get('code')

    if not codigo_bruto:
        return jsonify({"status": "erro", "msg": "Código vazio"}), 400

    # Mata o processo anterior se existir
    if bot_process:
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except:
            pass

    # Prepara a mensagem bonita de inicialização
    # Esse código abaixo será injetado antes do seu código para garantir a Embed
    logica_inicializacao = """
import discord
from discord.ext import commands
import asyncio

async def mensagem_bonita(bot):
    await bot.wait_until_ready()
    # Procura o primeiro canal de texto disponível para enviar a mensagem
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    title="🚀 Sistema XSSX Cloud Inicializado",
                    description="O seu bot foi hospedado e ligado com sucesso!",
                    color=0xff1a1a # Vermelho
                )
                embed.add_field(name="📡 Servidor", value="Render (Oregon)", inline=True)
                embed.add_field(name="⚙️ Engine", value="Python 3.10", inline=True)
                embed.set_image(url="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndnBqZ3BqZ3BqZ3BqZ3BqZ3BqZ3BqZ3BqZ3BqZ3BqZ3BqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/L3CtS6WKAnvL0UvWlP/giphy.gif")
                embed.set_footer(text="XSSX Host - Tecnologia de ponta")
                await channel.send(embed=embed)
                break
        break

# Injeção da lógica de boot
"""

    # Salva o arquivo final
    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(logica_inicializacao + codigo_bruto)
        # Adiciona a chamada da mensagem bonita ao final se o bot estiver definido
        f.write("\n\nif 'bot' in locals():\n    bot.loop.create_task(mensagem_bonita(bot))")

    try:
        # Inicia o processo de forma independente
        bot_process = subprocess.Popen(
            ["python", "bot_cliente.py"],
            preexec_fn=os.setsid
        )
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    print("✅ Núcleo XSSX Iniciado")
    run_flask()
