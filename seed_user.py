from app import app, db
from models import Student
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if user already exists
    if not Student.query.filter_by(usn='1RV23CS001').first():
        new_student = Student(
            name='Test User',
            usn='1RV23CS001',
            email='test@example.com',
            pin_hash=generate_password_hash('1234')
        )
        db.session.add(new_student)
        db.session.commit()
        print("User created: USN=1RV23CS001, PIN=1234")
    else:
        print("User already exists")
