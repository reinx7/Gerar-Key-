import os
import subprocess
import signal
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# Configuração do Servidor Web
app = Flask(__name__)
CORS(app)
bot_process = None 

@app.route('/')
def index():
    return "Núcleo XSSX Online e Aguardando Código!"

@app.route('/hospedar', methods=['POST'])
def hospedar():
    global bot_process
    data = request.json
    codigo = data.get('code') # Agora só pegamos o código

    if not codigo:
        return jsonify({"status": "erro", "msg": "Código ausente"}), 400

    # Se já existir um bot rodando, desliga ele
    if bot_process:
        try: os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except: pass

    # Cria o arquivo do bot EXATAMENTE como você colou no site
    with open("bot_cliente.py", "w", encoding="utf-8") as f:
        f.write(codigo)

    try:
        # Inicia o bot
        bot_process = subprocess.Popen(["python", "bot_cliente.py"], preexec_fn=os.setsid)
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

def run_flask():
    # O Render usa a porta 8080 por padrão
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # Inicia o servidor web
    print("⏳ Iniciando núcleo XSSX...")
    run_flask()
