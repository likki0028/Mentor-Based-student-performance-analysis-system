"""Test email with corrected email address."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "likhith23241a6796@grietcollege.com"
SENDER_PASSWORD = "bjjj fyvf wequ iqus"

out = open('email_test_result.txt', 'w')
def log(msg):
    print(msg)
    out.write(msg + '\n')
    out.flush()

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    server.ehlo()
    log("EHLO OK")
    server.starttls()
    log("STARTTLS OK")
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    log("LOGIN OK")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[AcademicVibe] Test Email Notification"
    msg["From"] = f"AcademicVibe <{SENDER_EMAIL}>"
    msg["To"] = "likhithbalaji90@gmail.com"
    plain = "This is a test email from AcademicVibe notification system. If you received this, email notifications are working!"
    msg.attach(MIMEText(plain, "plain"))
    
    server.sendmail(SENDER_EMAIL, "likhithbalaji90@gmail.com", msg.as_string())
    log("EMAIL SENT to likhithbalaji90@gmail.com")
    server.quit()
    log("DONE - SUCCESS")
except Exception as e:
    log(f"ERROR: {e}")

out.close()
