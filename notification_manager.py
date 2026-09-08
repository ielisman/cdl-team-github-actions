import firebase_admin
from firebase_admin import credentials, messaging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationManager:
    def __init__(self, firebase_cred_path=None):
        """
        Initialize the NotificationManager. Firebase is only initialized when
        a credentials path is given, so this class also works for email-only use.
        :param firebase_cred_path: Path to the Firebase service account JSON file.
        """
        if firebase_cred_path and not firebase_admin._apps:
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred)

    def send_firebase_notification(self, message_text, tokens=None):
        """
        Send a Firebase Cloud Messaging notification.

        :param message_text: Notification body text.
        :param tokens: Optional list of FCM registration tokens. Falls back to the
                       hardcoded default token (your phone) when None or empty.
        """
        # Hardcoded fallback — your phone. PWA-registered devices are passed via `tokens`.
        _default = "fjyfxJf9SnSBYvQ6vsoWNY:APA91bEJ1c1iyGpdFWmXZ7o-osReEYYqBu_41LsjICtL7MFs8qcjSybzklDlMFokzZwyPGjakJ1RnCeC_PvyNtneHWEjZR3ne-Ae5RKhgdrFQzcLwC0aMxE"
        send_to = [t for t in (tokens or [_default]) if t]
        if not send_to:
            print("No FCM tokens available. Skipping notification.")
            return
        try:
            if len(send_to) == 1:
                msg = messaging.Message(
                    notification=messaging.Notification(title="Road Test Alert", body=message_text),
                    token=send_to[0],
                )
                response = messaging.send(msg)
                print(f"Firebase notification sent: {response}")
            else:
                msg = messaging.MulticastMessage(
                    notification=messaging.Notification(title="Road Test Alert", body=message_text),
                    tokens=send_to,
                )
                response = messaging.send_each_for_multicast(msg)
                print(f"FCM multicast: {response.success_count} sent, {response.failure_count} failed")
        except Exception as e:
            print(f"Error sending Firebase notification: {e}")

    def send_email(self, from_email, app_password, to_email, subject, body):
        """
        Send an email via Gmail SMTP using an app password.
        :param from_email: Gmail address to send from.
        :param app_password: Gmail app password for from_email (not the account password).
        :param to_email: Recipient email address, or a list of recipient addresses.
        :param subject: Email subject.
        :param body: Email body.
        """
        try:
            to_addresses = [to_email] if isinstance(to_email, str) else list(to_email)

            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_addresses)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(from_email, app_password)
                server.send_message(msg, to_addrs=to_addresses)

            print(f"Email sent successfully to {', '.join(to_addresses)}")
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
                    result += f" {date} : {', '.join(times)}\n"  # Convert times list to comma-delimited string
        elif key == 'added_dates' and differences[key]:
            locations = differences[key]
            for location in locations:
                result += f"{location} (new dates are added)\n"
                for date, times in locations[location].items():
                    result += f" {date} : {', '.join(times)}\n"  # Convert times list to comma-delimited string
        elif key == 'added_times' and differences[key]:
            locations = differences[key]
            for location in locations:
                result += f"{location} (new times are added to exist dates)\n"
                for date, times in locations[location].items():
                    result += f" {date} : {', '.join(times)}\n"  # Convert times list to comma-delimited string

    if result:
        print(f"Sending notification\n{result}")
        firebase_cred_path = "./firebase_service_account.json"
        notification_manager = NotificationManager(firebase_cred_path)
        notification_manager.send_firebase_notification(result)
    else:
        print("No new time slots detected. No notification sent.")

if __name__ == "__main__":
    differences = {
        'same_times' : {},
        'added_locations': {
            'Nassau CC CDL': {
                '04/15/2025': ['No Slots']
            }
        },
        'added_dates': {},
        'added_times': {},
        'removed_locations': {},
        'removed_dates': {},
        'removed_times': {}
    }

    send_notification(differences)

