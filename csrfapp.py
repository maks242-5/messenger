from flask import Flask, request

app = Flask(__name__)

@app.route('/',methods=['POST'])
def index():
    user_outpot = request.form.get('username')
    transfer = request.form.get('num')
    #  Логіка пересилання коштів
    return f"Ви надіслали кошти на суму {transfer} користувачу {user_outpot} ."

if __name__ == '__main__':
    app.run(port=8000)