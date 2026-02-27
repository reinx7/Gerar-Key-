import os
import subprocess
import signal
from flask import Flask, request, jsonify
from flask_cors import CORS  # Importante para evitar erros de conexão
from threading import Thread
from bot_pai import bot as discord_bot # Importa o bot que criamos antes

app = Flask(__name__)
CORS(app) # Isso permite que o seu site fale com o Render sem bloqueios

bot_process = None 

@app.route('/')
def index():
    return "Servidor XSSX Online e Pronto!"

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    token = data.get('token')
    codigo = data.get('code')

    if not token or not codigo:
        return jsonify({"status": "erro", "msg": "Token ou Código ausentes"}), 400

    if bot_process:
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except:
            pass

    # Cria o arquivo do bot que você colou no site
    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(f"{codigo}\n\nbot.run('{token}')")

    try:
        bot_process = subprocess.Popen(["python", "bot_cliente.py"], preexec_fn=os.setsid)
        return jsonify({"status": "sucesso", "msg": "Bot Hospedado!"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)}), 500

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # 1. Liga o Servidor Web (para o site funcionar)
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # 2. Liga o Bot Pai (para o Discord funcionar)
    main_token = os.environ.get('DISCORD_TOKEN')
    if main_token:
        discord_bot.run(main_token)
    else:
        print("Aviso: Variável DISCORD_TOKEN não configurada no Render.")
        # Se não tiver token do bot pai, mantém o flask vivo
        while True: pass 
