import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://avnadmin:AVNS_xp2SiYh4HLQytUi6AmO@'
        'mysql-a2397a7-deliveryotter-3338.h.aivencloud.com:15862/goddo_poddo_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
