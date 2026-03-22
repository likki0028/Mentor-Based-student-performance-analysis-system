"""
Email service for sending branded notification emails via Gmail SMTP.
Also provides the legacy EmailService class for alert_service compatibility.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Gmail SMTP config
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "likhith23241a6796@grietcollege.com"
SENDER_PASSWORD = "bjjj fyvf wequ iqus"
SENDER_NAME = "MSPA System"


def get_email_template(title: str, message: str, link: str = None, priority: str = "low") -> str:
    """Generate branded HTML email template."""

    # Priority-based colors
    colors = {
        "low": {"bg": "#e0e7ff", "accent": "#6366f1", "icon": "ℹ️"},
        "medium": {"bg": "#fef3c7", "accent": "#f59e0b", "icon": "⚡"},
        "high": {"bg": "#fecaca", "accent": "#ef4444", "icon": "🚨"},
    }
    c = colors.get(priority, colors["low"])

    button_html = ""
    if link:
        button_html = f'''
        <div style="text-align: center; margin: 24px 0;">
            <a href="{link}" style="
                background: {c['accent']}; color: white; padding: 12px 32px;
                border-radius: 8px; text-decoration: none; font-weight: 700;
                font-size: 14px; display: inline-block;
            ">View Details →</a>
        </div>
        '''

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 560px; margin: 0 auto; padding: 24px;">
            <!-- Header -->
            <div style="
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                padding: 24px; border-radius: 12px 12px 0 0; text-align: center;
            ">
                <h1 style="margin: 0; color: white; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">
                    🎓 MSPA System
                </h1>
                <p style="margin: 4px 0 0; color: rgba(255,255,255,0.8); font-size: 12px;">
                    Student Performance Analysis System
                </p>
            </div>

            <!-- Content -->
            <div style="
                background: white; padding: 28px; border-radius: 0 0 12px 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            ">
                <!-- Priority Badge -->
                <div style="
                    background: {c['bg']}; color: {c['accent']};
                    padding: 8px 14px; border-radius: 8px; font-size: 12px;
                    font-weight: 700; display: inline-block; margin-bottom: 16px;
                ">
                    {c['icon']} {priority.upper()} PRIORITY
                </div>

                <h2 style="margin: 0 0 12px; color: #1f2937; font-size: 18px; font-weight: 700;">
                    {title}
                </h2>
                <p style="margin: 0 0 16px; color: #4b5563; font-size: 14px; line-height: 1.6;">
                    {message}
                </p>

                {button_html}

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="margin: 0; color: #9ca3af; font-size: 11px; text-align: center;">
                    This is an automated notification from MSPA System.<br>
                    GRIET College — Mentor-Based Student Performance Analysis System
                </p>
            </div>
        </div>
    </body>
    </html>
    '''


def send_email(to_email: str, title: str, message: str, link: str = None, priority: str = "low") -> bool:
    """Send a branded notification email. Returns True on success."""
    print(f"📧 send_email called: to={to_email}, title={title}, priority={priority}")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[MSPA System] {title}"
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = to_email

        plain = f"{title}\n\n{message}\n\n{'View: ' + link if link else ''}\n\n— MSPA System"
        msg.attach(MIMEText(plain, "plain"))

        html = get_email_template(title, message, link, priority)
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        print(f"✅ Email sent to {to_email}: {title}")
        return True
    except Exception as e:
        print(f"❌ Email failed to {to_email}: {e}")
        return False


def send_bulk_email(recipients: list, title: str, message: str, link: str = None, priority: str = "high") -> int:
    """
    Send the SAME email to multiple recipients using ONE SMTP connection.
    recipients: list of email strings.
    Returns the number of successfully sent emails.
    """
    if not recipients:
        return 0

    # De-duplicate and filter empty
    unique_emails = list(set(e for e in recipients if e))
    if not unique_emails:
        return 0

    print(f"📧 BULK EMAIL: sending to {len(unique_emails)} recipients, title={title}")

    # Build the email template once
    plain = f"{title}\n\n{message}\n\n{'View: ' + link if link else ''}\n\n— MSPA System"
    html = get_email_template(title, message, link, priority)

    sent = 0
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for email_addr in unique_emails:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = f"[MSPA System] {title}"
                    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
                    msg["To"] = email_addr
                    msg.attach(MIMEText(plain, "plain"))
                    msg.attach(MIMEText(html, "html"))

                    server.sendmail(SENDER_EMAIL, email_addr, msg.as_string())
                    sent += 1
                except Exception as e:
                    print(f"❌ Bulk email failed for {email_addr}: {e}")

        print(f"✅ Bulk email complete: {sent}/{len(unique_emails)} sent")
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")

    return sent


# --- Legacy EmailService class (used by alert_service.py) ---
class EmailService:
    @staticmethod
    def send_alert_email(to_email: str, student_name: str, alert_type: str, details: str):
        """Send an alert email to a mentor/faculty about a student issue."""
        if not to_email:
            return
        title = f"Alert: {alert_type} — {student_name}"
        message = f"Student {student_name} has triggered a {alert_type} alert.\n\n{details}"
        send_email(to_email, title, message, priority="high")


