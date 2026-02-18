import uuid
from datetime import datetime
from database import db

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    usn = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    pin_hash = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), default='student', nullable=False)
    credits = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "usn": self.usn,
            "email": self.email,
            "role": self.role,
            "credits": self.credits
        }

class Transaction(db.Model):
    txn_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    capacity_ml = db.Column(db.Integer, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "txn_id": self.txn_id,
            "capacity_ml": self.capacity_ml,
            "credits": self.credits,
            "is_used": self.is_used,
            "created_at": self.created_at.isoformat()
        }

class CreditTransfer(db.Model):
    transfer_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_usn = db.Column(db.String(20), nullable=False)
    receiver_usn = db.Column(db.String(20), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="pending") # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True) # Expiry time
    completed_at = db.Column(db.DateTime, nullable=True) # Completion time

    def to_dict(self):
        return {
            "transfer_id": self.transfer_id,
            "sender_usn": self.sender_usn,
            "receiver_usn": self.receiver_usn,
            "credits": self.credits,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "otp_code": self.otp_code,
            "expires_at": self.expires_at.isoformat(),
            "is_used": self.is_used
        }

class CreditHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    bottle_count = db.Column(db.Integer, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), default='credit', nullable=False) # credit, transfer, redeem
    session_id = db.Column(db.String(100), nullable=True) # Optional, for linking to specific session/transfer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bottle_count": self.bottle_count,
            "credits": self.credits,
            "type": self.type,
            "session_id": self.session_id,
            "date": self.created_at.isoformat() + "Z"
        }
