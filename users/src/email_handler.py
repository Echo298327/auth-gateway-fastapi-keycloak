import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


try:
    from config import settings
    from logger import init_logger

except ImportError:
    from .config import settings
    from .logger import init_logger

logger = init_logger('user.email')


def send_password_email(first_name, user_email, user_name, generated_password):
    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.APP_EMAIL
        message["To"] = user_email
        message["Subject"] = "Welcome to KalSense"

        html = f"""
        <html>
        <body>
        <p>Hi {first_name},<br>
        Welcome! Your new user was created with the following details:<br>
        Your user name is: <b>{user_name}</b><br>
        Your password is: <b>{generated_password}</b><br>
        Please change it upon your first login.<br>
        </p>
        <p>Best Regards,<br>
        <i>IT Services Team</i>
        </p>
        </body>
        </html>
        """

        part = MIMEText(html, "html")
        message.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(settings.APP_EMAIL, settings.APP_PASSWORD)
        text = message.as_string()
        server.sendmail(settings.APP_EMAIL, user_email, text)
        server.quit()
        logger.info(f"Email sent to {user_email}")
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email to {user_email}, error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}, error: {str(e)}")