from app import app, db
from models import Student
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if user already exists
    if not Student.query.filter_by(usn='1RV23CS002').first():
        new_student = Student(
            name='Receiver User',
            usn='1RV23CS002',
            email='receiver@example.com',
            pin_hash=generate_password_hash('1234')
        )
        db.session.add(new_student)
        db.session.commit()
        print("Receiver created: USN=1RV23CS002")
    else:
        print("Receiver already exists")
    
    # Also ensure the sender has credits
    sender = Student.query.filter_by(usn='1RV23CS001').first()
    if sender:
        sender.credits = 100 # Give some credits to test transfer
        db.session.commit()
        print(f"Added credits to Sender 1RV23CS001. Balance: {sender.credits}")
