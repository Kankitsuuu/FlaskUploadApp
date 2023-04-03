from flask.cli import FlaskGroup
from app import app, db
from models import Users
from werkzeug.security import generate_password_hash

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()
    print('DB successfully created')


@cli.command("create_superuser")
def create_superuser():
    try:
        add_user(True)
    except:
        print('Error')


@cli.command("create_user")
def create_user():
    try:
        add_user()
    except:
        print('Error')


@cli.command("delete_user")
def delete_user():
    username = input("Username: ")
    try:
        user = Users.query.filter_by(username=username).first()
        db.session.delete(user)
        db.session.commit()
    except:
        print('Error')


def add_user(is_admin: bool = False):
    username = input('Username: ')
    pswd = input('Password: ')
    pswd2 = input('Repeat password: ')
    while pswd != pswd2:
        print('Passwords is different')
        pswd2 = input('Repeat password: ')
    db.session.add(Users(username=username, password=generate_password_hash(pswd), is_admin=is_admin))
    db.session.commit()
    print('Successfully created')


if __name__ == "__main__":
    cli()
