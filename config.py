import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://avnadmin:AVNS_VCDCbC8zZJ25QBXJ9Z8@'
        'mysql-2f02e226-a96696713-98d4.f.aivencloud.com:12200/goddo_poddo_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
