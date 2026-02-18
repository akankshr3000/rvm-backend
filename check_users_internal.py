from app import app
from models import Student

with app.app_context():
    students = Student.query.all()
    print(f"Total Users: {len(students)}")
    for s in students:
        print(f"USN: {s.usn}, PIN Hash: {s.pin_hash}")
