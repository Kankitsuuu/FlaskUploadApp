from flask import Flask, render_template, url_for, request, flash, redirect, session, abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import DevelopmentConfig
from flask_migrate import Migrate
from forms import LoginForm
from UserLogin import UserLogin
import models

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db = SQLAlchemy(app)
login_manager = LoginManager(app)



context = {
                'title': 'Flask Upload App',
                'header': 'Welcome to Flask Upload App!',
                'menu': ['Пукнт 1', 'STEP 2'],
                'profile': {'name': 'Kankitsuuu', 'url': 'profile/kankitsuuu'}
               }


@app.route("/home")
@app.route("/")
def index():
    return render_template('content.html', **context)


@app.route("/profile/<username>")
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        abort(401)
    return f'It is {username}`s profile!'


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if len(request.form['user_name']) < 3:
            flash('Ошибка', category='error')
        else:
            flash('Сообщение отправлено', category='success')
    return render_template('upload.html')


@app.route('/login', methods=['POST', 'GET'])
def login():

    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    if form.validate_on_submit():
        user = models.Users.query.filter_by(username=form.username.data)
        print(user)
        if user and check_password_hash(user[0].password, form.password.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("upload"))

        flash("Incorrect login/password", "error")

    return render_template("login.html", title="Login", form=form)


@login_manager.user_loader
def load_user(user_id):
    print('Loading user')
    return UserLogin().from_db(user_id, db)


if __name__ == '__main__':
    app.run()
