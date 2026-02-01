import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)
load_dotenv()

# Configuration
EMAIL_ADDRESS = os.getenv("MAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
if EMAIL_PASSWORD:
    EMAIL_PASSWORD = EMAIL_PASSWORD.replace(' ', '')
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

print(f"DEBUG: Loaded Email: {EMAIL_ADDRESS}")
print(f"DEBUG: Password Length: {len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 0} (Should be 16)")

# Store messages in a JSON file
MESSAGES_FILE = 'messages.json'

def load_messages():
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=4)

def send_email(name, email, message):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"New Portfolio Contact from {name}"
        msg['Reply-To'] = email
        
        body = f"""
New contact form submission from your portfolio:

Name: {name}
Email: {email}

Message:
{message}

Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
       
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
       
        text = msg.as_string()
        print(f"Attempting to connect to Gmail...")
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

@app.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'Portfolio Backend API is running! 🚀',
        'version': '1.0',
        'endpoints': {
            'POST /api/contact': 'Submit contact form',
            'GET /api/messages': 'Get all messages',
            'GET /api/health': 'Check server health'
        }
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/contact', methods=['POST', 'OPTIONS'])
def contact():

    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data received'
            }), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not name or not email or not message:
            return jsonify({
                'status': 'error',
                'message': 'All fields are required'
            }), 400

        message_data = {
            'id': datetime.now().timestamp(),
            'name': name,
            'email': email,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        messages = load_messages()
        messages.append(message_data)
        save_messages(messages)
        
        print(f"Message saved: {message_data['id']}")
        
        email_sent = send_email(name, email, message)
        
        return jsonify({
            'status': 'success',
            'message': 'Your message has been sent successfully!',
            'email_sent': email_sent,
            'data': {
                'id': message_data['id'],
                'timestamp': message_data['timestamp']
            }
        }), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get all messages"""
    try:
        messages = load_messages()
        return jsonify({
            'status': 'success',
            'count': len(messages),
            'messages': sorted(messages, key=lambda x: x['timestamp'], reverse=True)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a specific message"""
    try:
        messages = load_messages()
        message_id = float(message_id)
        messages = [m for m in messages if m['id'] != message_id]
        save_messages(messages)
        
        return jsonify({
            'status': 'success',
            'message': 'Message deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/messages/<message_id>/read', methods=['PUT'])
def mark_as_read(message_id):
    """Mark message as read"""
    try:
        messages = load_messages()
        message_id = float(message_id)
        
        for msg in messages:
            if msg['id'] == message_id:
                msg['read'] = True
                break
        
        save_messages(messages)
        
        return jsonify({
            'status': 'success',
            'message': 'Message marked as read'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Portfolio Backend Server Starting...")
    print("=" * 50)
    print(f"📧 Email: {EMAIL_ADDRESS}")
    print(f"🌐 Server: http://localhost:3000")
    print(f"📝 API: http://localhost:3000/api/contact")
    print("=" * 50)
    print("\n⚠️  SETUP INSTRUCTIONS:")
    print("1. Update EMAIL_ADDRESS with your Gmail")
    print("2. Update EMAIL_PASSWORD with your App Password")
    print("3. Enable 'Less secure app access' or use App Password")
    print("\n💡 To get App Password:")
    print("   Google Account → Security → 2-Step Verification → App Passwords")
    print("=" * 50)
    print("\n✅ Server is ready! Waiting for requests...\n")
    
    app.run(debug=True, host='0.0.0.0', port=3000)