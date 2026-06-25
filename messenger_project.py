from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_  
import secrets  

from messenger_project_db import Session, Users, Friends, Messages

app = Flask(__name__)
app.secret_key = "supersecretkey"  

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  
app.config['MAX_FORM_MEMORY_SIZE'] = 1024 * 1024  
app.config['MAX_FORM_PARTS'] = 500

app.config['SECRET_KEY'] = '#cv)3v7w$*s3fk;5c!@y0?:?№3"9)#'

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    with Session() as session:
        user = session.query(Users).filter_by(id=user_id).first()
        if user:
            return user

@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('index.html', username=current_user.nickname)

@app.route('/', methods=["GET", "POST"])
def index():
    if "csrf_token" not in Session:
        Session ["csrf_token"] = secrets.token_hex(16)

    if request.method == "POST":
        form_token = request.form.get("csrf_token")
        if not form_token or form_token != Session["csrf_token"]:
            abort(403)  
        new_password = request.form.get("password")
        with Session() as session:
            user = session.query(Users).filter_by(id=current_user.id).first()
            if user:
                user.password = new_password
                session.commit()
        return redirect(url_for("success"))
    
    return render_template("index.html", user=current_user, csrf_token=Session["csrf_token"])

@app.route('/success')
def success():
    return render_template('success.html', user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']

        with Session() as session:
            user = session.query(Users).filter_by(nickname=nickname).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('home'))

            flash('Неправильний nickname або пароль!', 'danger')

    return render_template('login.html')


@app.route("/search_friends", methods=["GET", "POST"])
@login_required
def search_friends():
    if request.method == 'POST':
        user_search_name = request.form['name']
        with Session() as session:
            search_user = session.query(Users).filter_by(nickname=user_search_name).first()
            if search_user:
                check_request1 = session.query(Friends).filter_by(sender=search_user.id, recipient=current_user.id).first()
                check_request2 = session.query(Friends).filter_by(sender=current_user.id, recipient=search_user.id).first()

                if not check_request1 and not check_request2:
                    new_friend_request = Friends(sender=current_user.id, recipient=search_user.id, status=False)
                    session.add(new_friend_request)
                    session.commit()
                    flash("Запит на дружбу успішно надіслано!", 'success')
                else:
                    flash("Ви вже являєтеся друзями або між вами вже є активниз запит на дружбу", 'danger')
            else:
                flash("Користувача з таким нікнеймом не знайдено", 'danger')
    return render_template("search_friends.html")


@app.route('/friend_requests')
@login_required
def friend_requests():
    with Session() as session:
        all_friend_requests = session.query(Friends).filter_by(recipient=current_user.id, status=False).all()
        id_names_dict = {}
        for i in all_friend_requests:
            id_names_dict[i.sender_user.id] = i.sender_user.nickname
        return render_template('friend_requests.html', data=id_names_dict)


@app.route('/friend_requests_confirm', methods=["POST"])
@login_required
def friend_requests_confirm():
    request_sende_id = request.form['id']
    with Session() as session:
        select_request = session.query(Friends).filter_by(sender=request_sende_id, recipient=current_user.id, status=False).first()
        if not select_request:
            return 'Сталася помилка при підтвердженні'

        if request.form['result'] == 'yes':
            select_request.status = True
            session.commit()
        elif request.form['result'] == 'no':
            session.delete(select_request)
            session.commit()
        else:
            return redirect(url_for('home'))
    return redirect(url_for("friend_requests"))


@app.route("/my_friends")
@login_required
def my_friends():
    with Session() as session:
        all_friends1 = session.query(Friends).filter_by(sender=current_user.id, status=True).all()
        all_friends2 = session.query(Friends).filter_by(recipient=current_user.id, status=True).all()
        friend_names = []
        for i in all_friends1:
            friend_names.append(i.recipient_user.nickname)
        for i in all_friends2:
            friend_names.append(i.sender_user.nickname)
        return render_template("my_friends.html", data=friend_names)


@app.route('/delete_friend/<string:friend_name>', methods=["POST"])
@login_required
def delete_friend(friend_name):
    with Session() as session:
        friend = session.query(Users).filter_by(nickname=friend_name).first()
        friendship = session.query(Friends).filter(
            ((Friends.sender == current_user.id) & (Friends.recipient == getattr(friend, 'id', None))) | 
            ((Friends.sender == getattr(friend, 'id', None)) & (Friends.recipient == current_user.id))
        ).first() if friend else None
        
        if not friend or not friendship:
            flash('Користувача не знайдено' if not friend else 'Цей користувач не є вашим другом', 'danger')
            return redirect(url_for('my_friends'))
        
        session.delete(friendship)
        session.commit()
        flash(f'Користувача {friend_name} видалено з друзів', 'success')
    return redirect(url_for('my_friends'))


@app.route('/block_friend/<string:friend_name>', methods=["POST"])
@login_required
def block_friend(friend_name):
    with Session() as session:
        friend = session.query(Users).filter_by(nickname=friend_name).first()
        friendship = session.query(Friends).filter(
            ((Friends.sender == current_user.id) & (Friends.recipient == getattr(friend, 'id', None))) | 
            ((Friends.sender == getattr(friend, 'id', None)) & (Friends.recipient == current_user.id))
        ).first() if friend else None
        
        if not friend or not friendship:
            flash('Користувача не знайдено' if not friend else 'Цей користувач заблокований', 'danger')
            return redirect(url_for('my_friends'))
            
        session.delete(friendship)
        session.commit()
        flash(f'Користувача {friend_name} заблокано ', 'success')
    return redirect(url_for('my_friends'))


@app.route('/create_message/<string:user_name>', methods=["GET", "POST"])
@login_required
def create_message(user_name):
    if request.method == 'POST':
        message_text = request.form["text"]
        with Session() as session:
            user_recipient = session.query(Users).filter_by(nickname=user_name).first()
            if not user_recipient:
                flash('Отримувача не знайдено', 'danger')
                return render_template('create_message.html')

            check_request1 = session.query(Friends).filter_by(sender=user_recipient.id, recipient=current_user.id, status=True).first()
            check_request2 = session.query(Friends).filter_by(sender=current_user.id, recipient=user_recipient.id, status=True).first()
            if check_request1 or check_request2:
                new_message = Messages(sender=current_user.id, recipient=user_recipient.id, message_text=message_text)
                session.add(new_message)
                session.commit()
                flash("Повідомлення надіслано!", "success")
            else:
                flash("Отримувач не являється другом", "danger")
                return render_template('create_message.html')

    return render_template('create_message.html')


@app.route("/new_messages")
@login_required
def new_messages():
    with Session() as session:
        unread_messages = session.query(Messages).filter_by(recipient=current_user.id, status_check=False).all()
        
        name_text_dict = {}
        for i in unread_messages:
            nickname = i.sender_user.nickname
            if nickname not in name_text_dict:
                name_text_dict[nickname] = []
            name_text_dict[nickname].append(i.message_text)
            
            i.status_check = True
        
        session.commit()
        return render_template('new_messages.html', data=name_text_dict)


@app.route("/all_messages")
@login_required
def all_messages():
    with Session() as session:
        messages_list = session.query(Messages).filter_by(recipient=current_user.id).all()
        return render_template("all_messages.html", messages=messages_list)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        nickname = request.form['nickname']
        email = request.form['email']
        password = request.form['password']

        with Session() as session:
            user_exists = session.query(Users).filter(or_(Users.nickname == nickname, Users.email == email)).first()

            if user_exists:
                flash('Користувач з таким нікнеймом або email вже існує!', 'danger')
                return render_template('registr.html')
            
            new_user = Users(nickname=nickname, email=email)
            new_user.set_password(password)

            try:
                session.add(new_user)
                session.commit()
                flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
                return redirect(url_for('login'))
        
            except Exception as e:
                session.rollback()
                flash('Сталася помилка при реєстрації. Спробуйте ще раз.', 'danger')

    return render_template('registr.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)