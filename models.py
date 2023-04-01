from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db


class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<user id={self.id}>'

    def __str__(self):
        return self.username


class Files(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.LargeBinary)
    url = db.Column(db.String(255), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    fk = db.relationship('Users', backref='users', uselist=False)

    def __repr__(self):
        return f'<file id={self.id}'



