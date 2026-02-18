from flask import Blueprint, request, jsonify
from models import Student, CreditTransfer, CreditHistory, db
from werkzeug.security import check_password_hash
from routes.transactions import record_credit_history
import uuid
from datetime import datetime, timedelta

transfer_bp = Blueprint('transfer', __name__)

@transfer_bp.route('/transfer/create', methods=['POST'])
def create_transfer():
    data = request.json
    sender_usn = data.get('sender_usn')
    receiver_usn = data.get('receiver_usn')
    amount = data.get('amount')
    pin = data.get('pin')

    if not all([sender_usn, receiver_usn, amount, pin]):
        return jsonify({"error": "Missing fields"}), 400

    try:
        amount = int(amount)
        if amount <= 0:
             return jsonify({"error": "Amount must be positive"}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    sender = Student.query.filter_by(usn=sender_usn).first()
    receiver = Student.query.filter_by(usn=receiver_usn).first()

    if not sender:
        return jsonify({"error": "Sender not found"}), 404
    if not receiver:
         return jsonify({"error": "Receiver not found"}), 404
    
    if not check_password_hash(sender.pin_hash, str(pin)):
         return jsonify({"error": "Invalid PIN"}), 401
    
    # Check balance (Pre-check only, deduction happens at claim)
    if sender.credits < amount:
        return jsonify({"error": "Insufficient credits"}), 400

    # Create Pending Transfer
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    transfer = CreditTransfer(
        sender_usn=sender_usn,
        receiver_usn=receiver_usn,
        credits=amount,
        status="pending",
        expires_at=expires_at
    )
    
    db.session.add(transfer)
    db.session.commit()

    return jsonify({
        "message": "Transfer created",
        "transfer_id": transfer.transfer_id
    }), 201

@transfer_bp.route('/transfer/info/<transfer_id>', methods=['GET'])
def get_transfer_info(transfer_id):
    transfer = CreditTransfer.query.filter_by(transfer_id=transfer_id).first()
    
    if not transfer:
        return jsonify({"error": "Transfer not found"}), 404

    # Check expiry for display purposes
    is_expired = False
    if transfer.expires_at and datetime.utcnow() > transfer.expires_at:
        is_expired = True

    return jsonify({
        "transfer_id": transfer.transfer_id,
        "amount": transfer.credits,
        "sender_usn": transfer.sender_usn,
        "receiver_usn": transfer.receiver_usn,
        "status": transfer.status,
        "expires_at": transfer.expires_at.isoformat() if transfer.expires_at else None,
        "is_expired": is_expired
    }), 200

@transfer_bp.route('/transfer/claim', methods=['POST'])
def claim_transfer():
    data = request.json
    transfer_id = data.get('transfer_id')

    if not transfer_id:
        return jsonify({"error": "Missing transfer ID"}), 400

    # Start Atomic Transaction
    try:
        transfer = CreditTransfer.query.filter_by(transfer_id=transfer_id).with_for_update().first()

        if not transfer:
            return jsonify({"error": "Invalid transfer ID"}), 404
        
        if transfer.status == 'completed':
             return jsonify({"error": "Transfer already completed"}), 400
        
        if transfer.status != 'pending':
            return jsonify({"error": f"Transfer status is {transfer.status}"}), 400

        # Check Expiry
        if transfer.expires_at and datetime.utcnow() > transfer.expires_at:
            transfer.status = 'expired'
            db.session.commit()
            return jsonify({"error": "Transfer expired"}), 400

        sender = Student.query.filter_by(usn=transfer.sender_usn).with_for_update().first()
        receiver = Student.query.filter_by(usn=transfer.receiver_usn).with_for_update().first()

        if not sender or not receiver:
            return jsonify({"error": "User validation failed"}), 404
            
        # Re-check balance (Critical step)
        if sender.credits < transfer.credits:
            transfer.status = 'failed'
            db.session.commit()
            return jsonify({"error": "Sender has insufficient credits now"}), 400

        # Execute Transaction
        sender.credits -= transfer.credits
        receiver.credits += transfer.credits
        transfer.status = 'completed'
        transfer.completed_at = datetime.utcnow()

        # Record History
        record_credit_history(sender.id, 0, transfer.credits, session_id=transfer.transfer_id, txn_type='transfer')
        record_credit_history(receiver.id, 0, transfer.credits, session_id=transfer.transfer_id, txn_type='credit')

        db.session.commit()

        return jsonify({
            "message": "Transfer successful",
            "amount": transfer.credits,
            "sender_usn": sender.usn,
            "receiver_usn": receiver.usn,
            "date": transfer.completed_at.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Transaction failed: {str(e)}"}), 500

# Keep old endpoint for compatibility if needed, or remove? 
# The prompt implies REPLACING logic.
