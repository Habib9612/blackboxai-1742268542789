from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Required for CSRF
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trucknetic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens

# Set up CSRF protection
csrf = CSRFProtect(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# Database Models
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pickup_location = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pickup_location': self.pickup_location,
            'destination': self.destination,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# Exempt API endpoints from CSRF protection
@app.route('/api/book', methods=['POST'])
@csrf.exempt
def book_truck():
    try:
        data = request.get_json()
        logger.debug(f"Received booking request: {data}")
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No data provided'}), 400

        pickup_location = data.get('pickup_location')
        destination = data.get('destination')

        logger.debug(f"Pickup: {pickup_location}, Destination: {destination}")

        if not pickup_location or not destination:
            logger.error("Missing required fields")
            return jsonify({'error': 'Both pickup location and destination are required'}), 400

        new_booking = Booking(
            pickup_location=pickup_location,
            destination=destination
        )
        db.session.add(new_booking)
        db.session.commit()

        logger.info(f"Created new booking: {new_booking.to_dict()}")
        return jsonify({
            'message': 'Booking created successfully',
            'booking': new_booking.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
@csrf.exempt
def get_bookings():
    try:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        logger.debug(f"Retrieved {len(bookings)} bookings")
        return jsonify({
            'bookings': [booking.to_dict() for booking in bookings]
        })
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
