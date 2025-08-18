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

class AudioStory(db.Model):
    __tablename__ = 'tbl_audio_story'

    AUDIO_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CREATED_BY = db.Column(db.Integer, db.ForeignKey('tbl_users.id'))
    NAME = db.Column(db.String(255))
    LANGUAGE = db.Column(db.String(50))
    LINK_TYPE = db.Column(db.String(32))          # e.g., 'storyAvailable', 'poemAvailable', 'storyPoemNA'
    LINKED_STORY_ID = db.Column(db.Integer, nullable=True)  # FK to Story if linked
    LINKED_POEM_ID = db.Column(db.Integer, nullable=True)   # FK to Poem if linked
    AUDIO_URL = db.Column(db.String(255))
    TAGS = db.Column(db.Text)                      # Comma-separated tags
    STATUS = db.Column(db.String(20))
    CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow)
    UPDATED_ON = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AudioStory {self.NAME}>'

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

class Admin(db.Model):
    __tablename__ = 'tbl_admin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default='Active')  # <-- ADDED
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Password hashing
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "full_name": self.full_name,
    #         "email": self.email,
    #         "mobile": self.mobile,
    #         "role": self.role,
    #         "created_on": self.created_on.isoformat() if self.created_on else None,
    #         "updated_on": self.updated_on.isoformat() if self.updated_on else None
    #     }

class HelpSupport(db.Model):
    __tablename__ = 'tbl_help_support'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Serial in DataTable
    support_type = db.Column(db.String(100), nullable=False)  # e.g., "Technical Support", "Billing Inquiry"
    user_id = db.Column(db.Integer, db.ForeignKey('tbl_users.id'), nullable=False)  # Link to User
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending, Resolved, Rejected, Completed
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    admin_note = db.Column(db.Text)  # Note from admin when resolving/rejecting

    # Relationship to fetch user data
    user = db.relationship('User', backref=db.backref('help_support_requests', lazy=True))


    # def to_dict(self):
    #     """Convert DB record to dictionary for API response"""
    #     return {
    #         "id": self.id,
    #         "support_type": self.support_type,
    #         "user_name": self.user.full_name if self.user else None,
    #         "user_type": self.user.role if self.user else None,
    #         "created_on": self.created_on.strftime("%Y-%m-%d") if self.created_on else None,
    #         "status": self.status,
    #         "updated_on": self.updated_on.strftime("%Y-%m-%d") if self.updated_on else None,
    #         "admin_note": self.admin_note
    #     }
