from app import app, db
from models import Student
from werkzeug.security import generate_password_hash

with app.app_context():
    student = Student.query.filter_by(usn='1RV23CS001').first()
    if student:
        student.pin_hash = generate_password_hash('1234')
        db.session.commit()
        print(f"Password reset for {student.usn} to 1234")
    else:
        print("User not found")
