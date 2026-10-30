# Application User Classes File


# ------------------ imports -------------------------------------------------------------------------------------------


from flask_login import UserMixin


# ------------------ classes -------------------------------------------------------------------------------------------


# default user class
class User(UserMixin):
    def __init__(self, user_id, username, hashed_password):
        self.id = user_id
        self.username = username
        self.hashed_password = hashed_password
