import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_otp_email(to_email, otp_code):
    # Retrieve SMTP credentials from environment variables
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port_str = os.environ.get('SMTP_PORT', '587')
    smtp_port = int(smtp_port_str)
    
    sender_email = os.environ.get('SMTP_EMAIL')
    sender_password = os.environ.get('SMTP_PASSWORD')

    print(f"DTO-DEBUG: Attempting to send email to {to_email}")
    print(f"DTO-DEBUG: Server={smtp_server}:{smtp_port}")
    print(f"DTO-DEBUG: Sender={sender_email}")
    print(f"DTO-DEBUG: Password Length={len(sender_password) if sender_password else 0}")

    if not smtp_server:
        print("DTO-DEBUG: SMTP_SERVER not set")
        return False

    if not sender_email or not sender_password:
        print(f"DTO-DEBUG: Email credentials missing. OTP for {to_email} is {otp_code}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "Smart RVM - Reset PIN OTP"

        body = f"""
        <html>
        <body>
            <h2>Reset Your PIN</h2>
            <p>Your OTP to reset your PIN is: <strong>{otp_code}</strong></p>
            <p>This OTP is valid for 5 minutes.</p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        print("DTO-DEBUG: Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.set_debuglevel(1) # Enable SMTP debug output
        print("DTO-DEBUG: Starting TLS...")
        server.starttls()
        print("DTO-DEBUG: Logging in...")
        server.login(sender_email, sender_password)
        print("DTO-DEBUG: Sending mail...")
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"DTO-DEBUG: Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"DTO-DEBUG: Failed to send email: {e} - OTP: {otp_code}")
        import traceback
        traceback.print_exc()
        return False
