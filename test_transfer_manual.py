from app import app
from models import Student
from werkzeug.security import check_password_hash
from flask import json

def test_transfer():
    with app.test_client() as client:
        with app.app_context():
            sender_usn = "3BR23CS100"
            receiver_usn = "3BR23CS006" # Assuming this user exists or I'll find another
            
            # 1. Verify Database State
            sender = Student.query.filter_by(usn=sender_usn).first()
            if not sender:
                print(f"CRITICAL: Sender {sender_usn} NOT FOUND in DB!")
                return

            print(f"Sender: {sender.name} ({sender.usn})")
            print(f"Stored Hash: {sender.pin_hash}")
            
            # 2. Verify Hash Manually
            is_valid = check_password_hash(sender.pin_hash, "1234")
            print(f"Manual check_password_hash('1234'): {is_valid}")
            
            if not is_valid:
                print("CRITICAL: Stored hash does NOT match '1234'!")
                return

            # 3. Simulate Transfer Request
            payload = {
                "sender_usn": sender_usn,
                "receiver_usn": receiver_usn,
                "amount": 1,
                "pin": "1234" # Sending as string
            }
            
            print("\nSending Transfer Request...")
            response = client.post('/api/transfer/initiate', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.get_json()}")

if __name__ == "__main__":
    test_transfer()
