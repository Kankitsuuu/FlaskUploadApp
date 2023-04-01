import datetime
import os
from io import BytesIO

from flask import Flask, render_template, url_for, request, flash, redirect, session, abort, send_from_directory, \
    send_file
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import hashlib
from tzlocal import get_localzone
from config import DevelopmentConfig
from flask_migrate import Migrate
from forms import LoginForm
from UserLogin import UserLogin


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Login to view closed pages'
login_manager.login_message_category = 'success'



from models import Users, Files


@app.route("/home")
@app.route("/")
def index():
    context = {
        'title': 'Flask Upload App',
        'header': 'Welcome to Flask Upload App!',
        'menu': ['Пукнт 1', 'STEP 2'],
        'profile': {'name': 'Kankitsuuu', 'url': 'profile/kankitsuuu'}
    }
    return render_template('content.html', **context)


@app.route("/profile/<username>")
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        abort(401)
    return f'It is {username}`s profile!'


@app.route('/files', methods=['GET', 'POST'])
@login_required
def get_files():
    if request.method == 'POST':
        if '_upload' in request.form:
            print(request.files)
            file = request.files['file']
            if file and current_user.verify_filename(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    url = hashlib.sha256(file.filename.encode()).hexdigest()
                    ftype = filename.split('.')[-1].lower()
                    name = ''.join(filename.split('.')[0:-1])
                    new_file = Files(name=name,
                                     url=url,
                                     user_id=current_user.get_id(),
                                     ftype=ftype,
                                     upload_time=datetime.datetime.now(tz=get_localzone())
                                     )
                    db.session.add(new_file)
                    db.session.flush()
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    flash('File uploaded', 'success')
                except Exception as e:
                    flash('Add file error', 'error')
                    print(e)
                    db.session.rollback()
            else:
                flash('Invalible file type', 'error')
            db.session.commit()
        elif '_delete' in request.form:
            flash('Deleted', 'success')

    # else
    files = Files.query.all()
    user = Users.query.filter_by(id=current_user.get_id()).first()
    local_zone = get_localzone()
    return render_template('files.html', files=files, user=user, local_zone=local_zone)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_files'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("get_files"))

        flash("Incorrect login/password", "error")

    return render_template("login.html", title="Login", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/download/<file_url>')
@login_required
def download(file_url):
    try:
        file = Files.query.filter_by(url=file_url).first()
        filename = file.name + '.' + file.ftype
        with open(f"{app.config['UPLOAD_FOLDER']}/{filename}", 'rb') as file:
            data = file.read()
    except Exception as e:
        print(e)
        flash("Download file error", "error")
        return redirect(url_for('get_files'))

    return send_file(BytesIO(data),
                     download_name=filename, as_attachment=True)


@app.route('/delete/<file_url>')
@login_required
def delete_file(file_url):
    try:
        file = Files.query.filter_by(url=file_url).first()
        filename = file.name + '.' + file.ftype
        db.session.delete(file)
        os.remove(f"{app.config['UPLOAD_FOLDER']}/{filename}")
        db.session.commit()
        flash('Successfully deleted', 'success')
    except Exception as e:
        print(e)
        flash("Delete file error ", "error")
    return redirect(url_for('get_files'))


@login_manager.user_loader
def load_user(user_id):
    print('Loading user')
    user = Users.query.filter_by(id=user_id).first()
    return UserLogin().create(user)

