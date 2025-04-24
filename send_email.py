import smtplib
from email.message import EmailMessage
import os

# 🔒 Replace these with your actual email and app password
SENDER_EMAIL = "msughan.2005@gmail.com"
SENDER_PASSWORD = "qidb rbdo yjvj xlos"

def send_attendance_email(recipients, attachment_path):
    if not os.path.exists(attachment_path):
        print("❌ Attendance file not found.")
        return

    try:
        msg = EmailMessage()
        msg['Subject'] = '📋 Daily Attendance Report'
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(recipients)
        msg.set_content('Please find attached the attendance report for today.')

        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)

        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

        # Connect using TLS (port 587)
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.set_debuglevel(1)  # Enable debug output
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print("✅ Attendance email sent successfully.")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
