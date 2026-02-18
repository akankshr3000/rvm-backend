from datetime import datetime, timedelta
import random
import jwt
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import Student, OTP, Transaction, CreditHistory, db
from utils import send_otp_email
from routes.transactions import record_credit_history

auth_bp = Blueprint('auth', __name__)

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    usn = data.get('usn')
    email = data.get('email')
    email = data.get('email')
    pin = data.get('pin')
    role = data.get('role', 'student') # Default to student
    session_token = data.get('session_token')

    if not all([name, usn, email, pin]):
        return jsonify({"error": "Missing fields"}), 400

    # Check for existing user by USN or Email
    existing_user = Student.query.filter((Student.usn == usn) | (Student.email == email)).first()

    if existing_user:
        # User exists, verify PIN
        if not check_password_hash(existing_user.pin_hash, str(pin)):
             # If PIN matches, we log them in. If not, error.
             # Wait, strict security might say "User already exists". 
             # But user requested: "If yes -> fetch existing user".
             # We must verify PIN if we are "fetching" (logging in) an existing user via this form.
             return jsonify({"error": "User already exists. Incorrect PIN."}), 401
        
        # PIN Correct - Login
        # Update name if changed? Maybe not.
        token = create_token(existing_user.id)
        return jsonify({"message": "Login successful", "user": existing_user.to_dict(), "token": token}), 200

    # New User
    pin_hash = generate_password_hash(pin)
    new_student = Student(name=name, usn=usn, email=email, pin_hash=pin_hash, role=role, credits=0)
    
    earned_credits = 0
    if session_token:
        txn = Transaction.query.get(session_token)
        if txn and not txn.is_used:
            new_student.credits = txn.credits
            txn.is_used = True
            earned_credits = txn.credits
            # We need to add student first to get ID for history, but we can do it in one commit usually if we use object reference, 
            # but record_credit_history takes user_id. So flush first.
    
    db.session.add(new_student)
    db.session.flush() # Generate ID

    if earned_credits > 0:
        record_credit_history(new_student.id, 1, earned_credits, session_id=session_token)

    db.session.commit()

    token = create_token(new_student.id)
    return jsonify({
        "message": "Signup successful", 
        "user": new_student.to_dict(), 
        "token": token,
        "credits_earned": earned_credits
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    usn = data.get('usn')
    pin = data.get('pin')

    if not usn or not pin:
        return jsonify({"error": "Missing credentials"}), 400

    print(f"DEBUG LOGIN: Received USN={usn} (type={type(usn)}), PIN={pin} (type={type(pin)})")
    
    student = Student.query.filter_by(usn=usn).first()

    if not student:
        return jsonify({"error": "User not found", "error_code": "USER_NOT_FOUND"}), 404

    if not check_password_hash(student.pin_hash, str(pin)):
        return jsonify({"error": "Incorrect PIN", "error_code": "INVALID_PIN"}), 401

    token = create_token(student.id)
    return jsonify({"message": "Login successful", "user": student.to_dict(), "token": token}), 200

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    usn = data.get('usn')
    session_token = data.get('session_token')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    student = Student.query.filter_by(email=email).first()

    if not student:
        if not usn or not name:
             return jsonify({"error": "USN and Name required for new registration"}), 400
    try:
        student = Student.query.filter_by(email=email).first()

        if not student:
            if not usn or not name:
                return jsonify({"error": "USN and Name required for new registration"}), 400
            
            if Student.query.filter_by(usn=usn).first():
                return jsonify({"error": "USN already registered with another email"}), 400

            # Create new user with pin_hash = NULL
            student = Student(
                name=name,
                email=email,
                usn=usn,
                pin_hash=None, # Set to None as per instruction
                credits=0
            ) 
            
            earned_credits = 0
            if session_token:
                txn = Transaction.query.get(session_token)
                if txn and not txn.is_used:
                    student.credits = txn.credits
                    txn.is_used = True
                    earned_credits = txn.credits
            
            db.session.add(student)
            db.session.flush()

            if earned_credits > 0:
                record_credit_history(student.id, 1, earned_credits, session_id=session_token)

            db.session.commit()

            # Return with earned credits
            token = jwt.encode({
            'user_id': student.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")

            return jsonify({
                'token': token,
                'user': student.to_dict(),
                'requiresPinSetup': True,
                'credits_earned': earned_credits
            }), 200

        else: # Existing user
            if usn and student.usn != usn:
                return jsonify({"error": "USN mismatch. This email is linked to " + student.usn}), 403
            
            # Handle credit claim for existing user too if they just acted as "new" but existed
            earned_credits = 0
            if session_token:
                txn = Transaction.query.get(session_token)
                if txn and not txn.is_used:
                    student.credits += txn.credits
                    txn.is_used = True
                    earned_credits = txn.credits
                    record_credit_history(student.id, 1, earned_credits, session_id=session_token)
                    db.session.commit()

        
        # Generate Token
        token = jwt.encode({
            'user_id': student.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        # Check if PIN is set
        requires_pin = True if not student.pin_hash else False

        return jsonify({
            'token': token,
            'user': student.to_dict(),
            'requiresPinSetup': requires_pin,
            'credits_earned': earned_credits if 'earned_credits' in locals() else 0
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/set-pin', methods=['POST'])
def set_pin():
    data = request.json
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization token missing or invalid'}), 401
    token = auth_header.split(" ")[1]
    pin = data.get('pin')

    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({'error': 'Invalid PIN format'}), 400

    try:
        decoded = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user = Student.query.get(decoded['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        hashed_pin = generate_password_hash(pin)
        user.pin_hash = hashed_pin
        db.session.commit()
        
        return jsonify({'message': 'PIN set successfully', 'user': user.to_dict()}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid Token'}), 401
    except Exception as e:
        print(f"Error setting PIN: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@auth_bp.route('/user/<usn>', methods=['GET'])
def get_user(usn):
    student = Student.query.filter_by(usn=usn).first()
    if not student:
        return jsonify({"error": "User not found"}), 404
    return jsonify(student.to_dict()), 200

@auth_bp.route('/forgot-pin', methods=['POST'])
def forgot_pin():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # STRICT RULE 3: Check if user exists first
    student = Student.query.filter_by(email=email).first()
    if not student:
        # STRICT RULE 3: Return exact message "User not exists"
        return jsonify({"error": "User not exists"}), 404

    # STRICT RULE 5: Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Invalidate any previous unused OTPs for this email to prevent reuse/confusion
    existing_otps = OTP.query.filter_by(email=email, is_used=False).all()
    for otp in existing_otps:
        otp.is_used = True # Mark old ones as used/invalid

    otp_entry = OTP(email=email, otp_code=otp_code, expires_at=expires_at)
    db.session.add(otp_entry)
    db.session.commit()

    # STRICT RULE 5: Send OTP via SMTP
    email_sent = send_otp_email(email, otp_code)
    
    if not email_sent:
        return jsonify({"message": "Failed to send OTP email. Contact support."}), 500

    return jsonify({"message": "OTP sent successfully"}), 200

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp_code = data.get('otp')

    if not email or not otp_code:
        return jsonify({"error": "Email and OTP are required"}), 400

    otp_entry = OTP.query.filter_by(email=email, otp_code=otp_code, is_used=False).order_by(OTP.created_at.desc()).first()

    if not otp_entry:
        return jsonify({"error": "Invalid OTP"}), 400

    if datetime.utcnow() > otp_entry.expires_at:
        return jsonify({"error": "OTP expired"}), 400

    return jsonify({"message": "OTP verified"}), 200

@auth_bp.route('/reset-pin', methods=['POST'])
def reset_pin():
    data = request.json
    email = data.get('email')
    otp_code = data.get('otp')
    new_pin = data.get('new_pin')

    if not all([email, otp_code, new_pin]):
        return jsonify({"error": "Missing fields"}), 400

    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"error": "PIN must be 4 digits"}), 400

    # Verify OTP again (atomic operation)
    otp_entry = OTP.query.filter_by(email=email, otp_code=otp_code, is_used=False).order_by(OTP.created_at.desc()).first()

    if not otp_entry:
        return jsonify({"error": "Invalid or used OTP"}), 400

    if datetime.utcnow() > otp_entry.expires_at:
        return jsonify({"error": "OTP expired"}), 400

    student = Student.query.filter_by(email=email).first()
    if not student:
        return jsonify({"error": "User not found"}), 404

    # Update PIN
    student.pin_hash = generate_password_hash(new_pin)
    otp_entry.is_used = True # Mark used now
    
    db.session.commit()

    return jsonify({"message": "PIN reset successful"}), 200
