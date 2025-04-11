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
        # this is token for my phone. Get tokens for other phones as well
        token = "fjyfxJf9SnSBYvQ6vsoWNY:APA91bEJ1c1iyGpdFWmXZ7o-osReEYYqBu_41LsjICtL7MFs8qcjSybzklDlMFokzZwyPGjakJ1RnCeC_PvyNtneHWEjZR3ne-Ae5RKhgdrFQzcLwC0aMxE"
        try:
            # Prepare the notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Road Test Notification",
                    body=differences
                ),                
                token=token # topic="rt-updates"  # Replace with your topic name
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

# firebase_cred_path = "./firebase_service_account.json"
# notification_manager = NotificationManager(firebase_cred_path)

# differences = {
#     "added_locations": {"Nice Test Area CDL": {"03/31/2025": ["8:30", "9:30"]}},
#     "added_dates": {},
#     "added_times": {}
# }
# notification_manager.send_firebase_notification(
#     "Nice Test Area CDL 1\n  03/31/2025 8:30, 9:30\nNice Test Area CDL 3\n  03/31/2025 12:45")

def send_notification(differences):
    """
    Send a notification when new or changed time slots are detected.
    """    
    result = ""
    for key in differences:
        if key == 'added_locations' and differences[key]:
            locations = differences[key]
            for location in locations:
                result += f"{location}\n"
                for date, times in locations[location].items():
                    result += f" {date} : {times}\n"
        elif key == 'added_dates' and differences[key]:
            locations = differences[key]
            for location in locations:
                result += f"{location} (new dates are added)\n"
                for date, times in locations[location].items():
                    result += f" {date} : {times}\n"
        elif key == 'added_times' and differences[key]:
            locations = differences[key]
            for location in locations:
                result += f"{location} (new times are added to exist dates)\n"
                for date, times in locations[location].items():
                    result += f" {date} : {times}\n"

    if result:
        print(f"Sending notification\n{result}")
        firebase_cred_path = "./firebase_service_account.json"
        notification_manager = NotificationManager(firebase_cred_path)
        notification_manager.send_firebase_notification(result)
    else:
        print("No new time slots detected. No notification sent.")

differences = {
    'same_times' : {},
    'added_locations': {
        'Nassau CC CDL': {
            '04/15/2025': ['12:45 PM']
        }
    },
    'added_dates': {},
    'added_times': {},
    'removed_locations': {},
    'removed_dates': {},
    'removed_times': {}
}

#send_notification(differences)

