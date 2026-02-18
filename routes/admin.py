from flask import Blueprint, jsonify, request, current_app
from models import Student, Transaction, CreditHistory, OTP, CreditTransfer, db
import jwt
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Student.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@admin_bp.route('/reset', methods=['POST'])
@token_required
def reset_system(current_user):
    if current_user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403

    try:
        # Delete non-admin users
        db.session.query(Student).filter(Student.role != 'admin').delete()
        
        # Delete all other data
        db.session.query(Transaction).delete()
        db.session.query(CreditHistory).delete()
        db.session.query(OTP).delete()
        db.session.query(CreditTransfer).delete()
        
        db.session.commit()
        return jsonify({"message": "System reset successful"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
