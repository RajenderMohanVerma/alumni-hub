
import os
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

print(f"Mail Server: {app.config['MAIL_SERVER']}")
print(f"Mail Port: {app.config['MAIL_PORT']}")
print(f"Mail Username: {app.config['MAIL_USERNAME']}")
print(f"Mail Password Set: {'Yes' if app.config['MAIL_PASSWORD'] else 'No'}")

with app.app_context():
    try:
        msg = Message(
            subject='Test Email from Alumni Hub Debugger',
            recipients=[app.config['MAIL_USERNAME']], # Send to self
            body='This is a test email to verify SMTP configuration.'
        )
        print("Attempting to send email...")
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        with open('email_test.log', 'w') as f:
            f.write(f"Mail Server: {app.config['MAIL_SERVER']}\n")
            f.write(f"Mail Port: {app.config['MAIL_PORT']}\n")
            f.write(f"Mail Username: {app.config['MAIL_USERNAME']}\n")
            f.write(f"Error: {e}\n")
            import traceback
            traceback.print_exc(file=f)
        print(f"Failed to send email. Error: {e}")
