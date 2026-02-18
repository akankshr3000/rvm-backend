import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from models import Transaction, Student, CreditHistory, db
from werkzeug.security import check_password_hash
import random

txn_bp = Blueprint('transactions', __name__)

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

@txn_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    history = CreditHistory.query.filter_by(user_id=current_user.id).order_by(CreditHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history]), 200

def record_credit_history(user_id, bottle_count, credits, session_id=None, txn_type='credit'):
    history = CreditHistory(
        user_id=user_id,
        bottle_count=bottle_count,
        credits=credits,
        type=txn_type,
        session_id=session_id
    )
    db.session.add(history)

@txn_bp.route('/transaction/create', methods=['POST'])
def create_transaction():
    # Simulation: Create a transaction with random bottle capacity
    capacities = [250, 500, 750, 1000]
    capacity = random.choice(capacities)
    credits = int(capacity / 10) 

    new_txn = Transaction(capacity_ml=capacity, credits=credits)
    db.session.add(new_txn)
    db.session.commit()

    return jsonify(new_txn.to_dict()), 201

@txn_bp.route('/transaction/<txn_id>', methods=['GET'])
def get_transaction(txn_id):
    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({"error": "Transaction not found"}), 404
    
    return jsonify(txn.to_dict()), 200

@txn_bp.route('/claim', methods=['POST'])
@token_required
def claim_credits(current_user):
    data = request.json
    txn_id = data.get('txn_id')
    
    if not txn_id:
        return jsonify({"error": "Missing transaction ID"}), 400

    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({"error": "Invalid transaction ID"}), 404
    
    if txn.is_used:
        return jsonify({"error": "Transaction already claimed"}), 400

    # Update balances
    current_user.credits += txn.credits
    txn.is_used = True
    
    # Insert History
    record_credit_history(current_user.id, 1, txn.credits, session_id=txn.txn_id, txn_type='credit')
    
    db.session.commit()

    return jsonify({
        "message": "Credits claimed successfully",
        "credits_added": txn.credits,
        "new_balance": current_user.credits
    }), 200
