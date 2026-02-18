import sys
from app import app
from models import Student, db

def set_admin_role(email):
    with app.app_context():
        user = Student.query.filter_by(email=email).first()
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"SUCCESS: User {email} is now an ADMIN.")
        else:
            print(f"ERROR: User {email} not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
    else:
        set_admin_role(sys.argv[1])
