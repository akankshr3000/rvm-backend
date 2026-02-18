from models import Student
from database import db
from app import app
from werkzeug.security import generate_password_hash

with app.app_context():
    # User from earlier logs: 3BR23CS006
    # User from screenshot: 3BR23CS100
    
    # Check 006
    user006 = Student.query.filter_by(usn="3BR23CS006").first()
    if user006:
        print(f"User 006 found: {user006.name} ({user006.usn})")
        print(f"Stored Hash: {user006.pin_hash}")
        # Reset PIN to 1234
        user006.pin_hash = generate_password_hash("1234")
        db.session.commit()
        print("Reset PIN for 3BR23CS006 to '1234'")

    # Check 100
    user100 = Student.query.filter_by(usn="3BR23CS100").first()
    if user100:
        print(f"User 100 found: {user100.name} ({user100.usn})")
        print(f"Stored Hash: {user100.pin_hash}")
        # Reset PIN to 1234
        user100.pin_hash = generate_password_hash("1234")
        db.session.commit()
        print("Reset PIN for 3BR23CS100 to '1234'")
    else:
        print("User 3BR23CS100 not found.")
