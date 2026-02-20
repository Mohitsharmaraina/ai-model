from config_secrets import settings
from smtplib import SMTP
from email.mime.text import MIMEText
from ssl import create_default_context

def send_mail(data: dict | None = None):
    if data is None:
        return

    # Create the email content
    subject = data.get("subject", "No Subject")
    body = data.get("body", "No Content")
    recipient_email = data.get("recipient_email")

    if not recipient_email:
        raise ValueError("Recipient email is required")

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = settings.mail_username
    msg['To'] = ",".join(recipient_email) if isinstance(recipient_email, list) else recipient_email

    # Send the email using SMTP
    context = create_default_context()
    
    try:
        with SMTP(settings.mail_host, settings.mail_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.mail_username, settings.mail_password)
            server.send_message(msg)
            server.quit()
        return {"status": 200, "message": "Email sent successfully"}
    except Exception as e:
        return {"status": 500, "message": f"Failed to send email: {str(e)}"}