from app import app
from models import Student, db
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create DEMO_RECEIVER if not exists
    demo_usn = "DEMO_RECEIVER"
    demo_user = Student.query.filter_by(usn=demo_usn).first()
    
    if not demo_user:
        try:
            demo_user = Student(
                name="Demo Receiver",
                usn=demo_usn,
                email="demo_receiver@example.com",
                pin_hash=generate_password_hash("1234"),
                role="student",
                credits=100
            )
            db.session.add(demo_user)
            db.session.commit()
            print(f"Created user: {demo_usn}")
        except Exception as e:
            print(f"Error creating user: {e}")
            db.session.rollback()
    else:
        print(f"User {demo_usn} already exists.")
