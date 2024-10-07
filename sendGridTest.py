# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
import sendgrid

data = {
    "content": [
        {
            "type": "text/html",
            "value": "<html><p>SendGrid API Test with Reply To!</p></html>"
        }
    ],
    "from": {
        "email": "info@redhookcdl.com",
        "name": "Red Hook Driving School"
    },
    "reply_to": {
        "email": "redhookcdl@gmail.com",
        "name": "Red Hook Driving School G"
    },
    "personalizations": [
    {
      "to": [
        {
          "email": "ielisman@gmail.com"
        }
      ],
      "subject": "Sending with SendGrid is Fun"
    }
  ],
}

sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
response = sg.client.mail.send.post(request_body=data)
print(response.status_code)
print(response.body)
print(response.headers)

# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail

# message = Mail(
#     from_email='info@redhookcdl.com',
#     to_emails='ielisman@gmail.com',
#     subject='Testing sendGrid',
#     html_content='<strong>SendGrid APT Test</strong>')

# try:
#     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
#     response = sg.send(message)
#     print(response.status_code)
#     print(response.body)
#     print(response.headers)
# except Exception as e:
#     print(e.message)