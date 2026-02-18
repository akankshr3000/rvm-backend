from flask import Blueprint, jsonify
from sqlalchemy import func
from models import Student, CreditHistory, db

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/system-analytics', methods=['GET'])
def get_system_analytics():
    try:
        # Total Students
        total_students = Student.query.count()

        # Total Logged In Users (Users with at least one credit history)
        # using distinct user_id from CreditHistory
        # SQLAlchemy 1.4/2.0+ distinct count:
        total_logged_in_users = db.session.query(func.count(func.distinct(CreditHistory.user_id))).scalar()

        # Total Credits Distributed (type='credit')
        # Filter for type='credit' if column exists, otherwise just all credits (older implementation assumption)
        # Since we added 'type' recently, we should check for it.
        # However, safe implementation:
        try:
            total_credits_distributed = db.session.query(func.sum(CreditHistory.credits)).filter(CreditHistory.type == 'credit').scalar()
        except Exception:
            # Fallback if migration hasn't run or type column issue (though we did run migration)
            total_credits_distributed = db.session.query(func.sum(CreditHistory.credits)).scalar()
        
        total_credits_distributed = total_credits_distributed or 0

        # Total Transactions (all types)
        total_transactions = CreditHistory.query.count()

        # Student List
        students_data = []
        students = Student.query.all()
        
        for student in students:
            # Get transaction count for this student
            txn_count = CreditHistory.query.filter_by(user_id=student.id).count()
            
            # Get last activity
            last_activity = CreditHistory.query.filter_by(user_id=student.id).order_by(CreditHistory.created_at.desc()).first()
            last_activity_date = last_activity.created_at.isoformat() if last_activity else None

            students_data.append({
                "name": student.name,
                "usn": student.usn,
                "current_credits": student.credits,
                "total_transactions": txn_count,
                "last_activity_date": last_activity_date
            })

        # Sort by current_credits descending
        students_data.sort(key=lambda x: x['current_credits'], reverse=True)

        return jsonify({
            "total_students": total_students,
            "total_logged_in_users": total_logged_in_users,
            "total_credits_distributed": total_credits_distributed,
            "total_transactions": total_transactions,
            "students": students_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
