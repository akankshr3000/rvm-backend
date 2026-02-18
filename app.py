from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '.env')) # Load environment variables from .env file in backend directory
from database import db, init_db
from routes.auth import auth_bp
from routes.transactions import txn_bp
from routes.transfer import transfer_bp

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'rvm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key' # Change for production

# Enable CORS for all domains, specifically allowing headers and methods
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

init_db(app)

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(txn_bp, url_prefix='/api')
app.register_blueprint(transfer_bp, url_prefix='/api')

from routes.analytics import analytics_bp
app.register_blueprint(analytics_bp, url_prefix='/api')

from routes.admin import admin_bp
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route("/api/test")
def test():
    return {"message": "Backend working"}
 
if __name__ == '__main__':
    app.run(port=5000, debug=True)
