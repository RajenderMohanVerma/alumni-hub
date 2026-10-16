"""Send a safe SMTP configuration test to the configured sender or recipient."""

import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / '.env')

host = os.getenv('MAIL_SERVER', 'smtp.gmail.com').strip()
port = int(os.getenv('MAIL_PORT', '587'))
username = os.getenv('MAIL_USERNAME', '').strip()
password = ''.join(os.getenv('MAIL_PASSWORD', '').split())
recipient = os.getenv('MAIL_TEST_RECIPIENT', username).strip()
use_tls = os.getenv('MAIL_USE_TLS', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
use_ssl = os.getenv('MAIL_USE_SSL', 'false').strip().lower() in ('1', 'true', 'yes', 'on')
placeholders = {
    'paste-your-gmail-address',
    'paste-your-16-char-app-password',
    'your.address@gmail.com',
    'your-16-char-google-app-password',
}

if (not username or not password or not recipient
        or username.lower() in placeholders
        or password.lower() in placeholders
        or username.lower().startswith('paste-your-')
        or password.lower().startswith('paste-your-')):
    print('Email is not configured. Set MAIL_USERNAME and MAIL_PASSWORD in .env first.')
    sys.exit(1)

message = EmailMessage()
message['Subject'] = 'Alumni Hub SMTP configuration test'
message['From'] = f'ALUMNI HUB <{username}>'
message['To'] = recipient
message.set_content('SMTP configuration is working for Alumni Hub.')

try:
    if use_ssl:
        smtp = smtplib.SMTP_SSL(host, port, timeout=15, context=ssl.create_default_context())
    else:
        smtp = smtplib.SMTP(host, port, timeout=15)

    with smtp as server:
        if use_tls and not use_ssl:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        server.login(username, password)
        server.send_message(message)
    print('SMTP test email sent successfully.')
except smtplib.SMTPAuthenticationError:
    print('SMTP rejected the credentials. Check MAIL_USERNAME and the Gmail App Password.')
    sys.exit(1)
except (smtplib.SMTPException, OSError, TimeoutError):
    print('SMTP delivery failed. Check the SMTP host, port, TLS settings, and network.')
    sys.exit(1)
