import firebase_admin
from firebase_admin import credentials, messaging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationManager:
    def __init__(self, firebase_cred_path):
        """
        Initialize the NotificationManager with Firebase credentials.
        :param firebase_cred_path: Path to the Firebase service account JSON file.
        """
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)

    def send_firebase_notification(self, differences):
        """
        Send a Firebase Cloud Messaging notification with the differences hash.
        :param differences: The differences hash to include in the notification.
        """
        try:
            # Prepare the notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Road Test Notification",
                    body=f"RT Updates:\n{differences}"
                ),
                topic="rt-updates"  # Replace with your topic name
            )

            # Send the notification
            response = messaging.send(message)
            print(f"Firebase notification sent successfully: {response}")
        except Exception as e:
            print(f"Error sending Firebase notification: {e}")

    def send_email(self, to_email, subject, body):
        """
        Send an email using Gmail.
        :param to_email: Recipient email address.
        :param subject: Email subject.
        :param body: Email body.
        """
        try:
            # Gmail credentials
            from_email = "info@redhookcdl.com"
            app_password = "your-app-password"  # Replace with your Gmail app password

            # Set up the email message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Connect to Gmail SMTP server and send the email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(from_email, app_password)
                server.send_message(msg)

            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Error sending email: {e}")