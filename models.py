from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'tbl_users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))  # ⛔️ Removed unique=True
    mobile = db.Column(db.String(15))
    password = db.Column(db.String(255))
    role = db.Column(db.String(20))  # 'Writer', 'Reader', etc.
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('email', 'role', name='unique_email_role'),  # ✅ Composite unique constraint
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Story(db.Model):
    __tablename__ = 'tbl_story'
    STORY_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WRITTEN_BY = db.Column(db.Integer, db.ForeignKey('tbl_users.id'))
    NAME = db.Column(db.String(255))
    LANGUAGE = db.Column(db.String(50))
    FONT = db.Column(db.String(50))
    PDF_URL = db.Column(db.String(255))
    STORY = db.Column(db.Text)
    STATUS = db.Column(db.String(20))
    CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow)
    UPDATED_ON = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    PRICE = db.Column(db.Numeric(10, 2))
    TAGS = db.Column(db.Text)  # Newly added column


class Poem(db.Model):
    __tablename__ = 'tbl_poem'
    STORY_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WRITTEN_BY = db.Column(db.Integer, db.ForeignKey('tbl_users.id'))
    NAME = db.Column(db.String(255))
    LANGUAGE = db.Column(db.String(50))
    FONT = db.Column(db.String(50))
    PDF_URL = db.Column(db.String(255))
    STORY = db.Column(db.Text)
    STATUS = db.Column(db.String(20))
    CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow)
    UPDATED_ON = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    PRICE = db.Column(db.Numeric(10, 2))
    TAGS = db.Column(db.Text)  # Newly added column
