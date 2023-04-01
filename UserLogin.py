from flask_login import UserMixin
from config import Config


class UserLogin(UserMixin):

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user.id)

    def verify_filename(self, filename: str):
        ext = filename.rsplit('.')[-1].lower()
        print(ext)
        if ext in Config.ALLOWED_EXTENSIONS:
            return True
        return False
