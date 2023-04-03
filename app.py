import datetime
import os
from io import BytesIO
import sqlalchemy.exc
from flask import Flask, render_template, url_for, request, flash, redirect, session, abort, send_from_directory, \
    send_file
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import hashlib
import pytz
from config import DevelopmentConfig
from flask_migrate import Migrate
from forms import LoginForm
from UserLogin import UserLogin
import time

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Login to view closed pages'
login_manager.login_message_category = 'success'

from models import Users, Files


@app.route("/")
@login_required
def home():
    return redirect(url_for('get_files', page=1))


@app.route('/files/<int:page>', methods=['GET', 'POST'])
@login_required
def get_files(page=1):
    if request.method == 'POST':
        if '_upload' in request.form:
            file = request.files['file']
            if file and current_user.verify_filename(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    url = hashlib.sha256(file.filename.encode()).hexdigest()
                    ftype = filename.split('.')[-1].lower()
                    name = '.'.join(filename.split('.')[0:-1])
                    new_file = Files(name=name,
                                     url=url,
                                     user_id=current_user.get_id(),
                                     ftype=ftype,
                                     upload_time=datetime.datetime.now(tz=pytz.timezone(os.environ.get('TZ')))
                                     )
                    db.session.add(new_file)
                    db.session.flush()
                    start = time.time()
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    t_diff = time.time() - start
                    flash(f'File uploaded in {t_diff:.4f} sec', 'success')
                except sqlalchemy.exc.IntegrityError:
                    flash('File with this name already exists', 'error')
                    db.session.rollback()
                except Exception as e:
                    flash('Add file error', 'error')
                    print(e)
                    print(type(e))
                    db.session.rollback()
            else:
                flash('Invalible file type', 'error')
            db.session.commit()

    # else
    files = Files.query.order_by(Files.upload_time.desc()).paginate(page=page, per_page=8, error_out=True, count=True)
    user = Users.query.get(current_user.get_id())
    tz = pytz.timezone(os.environ.get('TZ'))
    return render_template('files.html', files=files, user=user, tz=tz)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_files', page=1))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("get_files", page=1))
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
        return redirect(url_for('get_files', page=1))

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
    return redirect(url_for("get_files", page=1))


@app.errorhandler(413)
def file_too_large(error):
    flash('File too large. Max size: 16 Mb.', 'error')
    return redirect(request.url)


@login_manager.user_loader
def load_user(user_id):
    print('Loading user')
    user = Users.query.get(user_id)
    return UserLogin().create(user)

