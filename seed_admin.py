import os
from app import app
from models import db, Admin

SUPER_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "admin@example.com")
SUPER_PWD = os.getenv("SUPER_ADMIN_PASSWORD", "ChangeThisPass123!")
SUPER_FULLNAME = os.getenv("SUPER_ADMIN_NAME", "Super Admin")
SUPER_MOBILE = os.getenv("SUPER_ADMIN_MOBILE", "0000000000")

with app.app_context():
    # Only create if there isn't already a super_admin
    existing = Admin.query.filter_by(role="super_admin").first()
    if not existing:
        admin = Admin(
            full_name=SUPER_FULLNAME,
            email=SUPER_EMAIL,
            mobile=SUPER_MOBILE,
            role="super_admin"
        )
        admin.set_password(SUPER_PWD)
        db.session.add(admin)
        db.session.commit()
        print("Super admin created:", SUPER_EMAIL)
    else:
        print("Super admin already exists:", existing.email)
