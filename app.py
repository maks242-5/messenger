from flask import Flask

app = Flask(__name__)
from flask import Flask, request, make_response
import secrets
app = Flask(__name__)

@app.after_request
def apply_csp(response):
    nonce = secrets.token_urlsafe(16)  # Генеруємо випадковий nonce для дозволених скриптів
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    response.set_cookie('nonce', nonce)
    return response

@app.route('/')
def index():
    user_name = request.args.get('username', '')
    user_code = request.args.get('user_code', '')

    # Логіка сайту, використання вписаних даних.

    html = f"""
    <html>
        <body>
            <h1>Ласкаво просимо, користувач!</h1>
            <form method="GET">
                <p>Введіть нікнейм</p>
                <input type="text" name="username">
                <p>Введіть свій код доступу:</p>
                <input type="text" name="user_code">
                <input type="submit" value="Надіслати">
            </form>
            <div>Дякуємо! {user_name}</div>
        </body>
    </html>
    """
    response = make_response(html)
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)