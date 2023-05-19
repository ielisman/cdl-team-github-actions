import base64
import firebase_admin
import os
import sys
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

url = ""
if (len(sys.argv) > 2):
  url = sys.argv[2]
else:
  print("URL is not supplied. Quiting")
  quit()
  
private_key_str = os.environ['CDL_TEAM_KEY']
private_key = RSA.import_key(private_key_str)
encrypted_message = 'JHrSklI0NQ7ZwqVHrr7AMvU3X9R3znWOyT4+4hkpDsHGq00+QycRYT1E2tTw0OqefsJd5bdTvjj5YXyRKeb01g1J6LDy7QXIo1H+wSqfO1OwZv3RsaF/V/mx19JLoAtjYkqW6Fm1xAo/PgTuXbAUaOj8eUptSVU1pbT4Wxle8eAW6/LZAZtDBTbgnGPpfeUhpMIPPI/JOAsVk60z+T5QatApW54Keo1+l/qfmgg1eEhZVkLkPqsLiCeYoEPEzRe6XwMdv7EmADcJBvqv6iXwPRMvFiCmu4wPiWw/CxXf2XC5pAuyfRGVAgeQh4u17DjaExbUFDJP3UbUTYX3k82iUw=='
cipher_rsa = PKCS1_OAEP.new(private_key)
message_bytes = base64.b64decode(encrypted_message)
decrypted_message = cipher_rsa.decrypt(message_bytes).decode()  
  
firebase_credentials = os.environ['FIREBASE_JSON']
firebase_creds_file = 'firebase-creds.json'
with open(firebase_creds_file, 'w') as file:
    file.write(firebase_credentials)
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()
doc_ref = db.collection('messages').document()
doc_ref.set({
    'message': decrypted_message
})  

# Configure Chrome options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

# Initialize the Chrome webdriver with WebDriver Manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Navigate to the website URL
driver.get(url)

# Retrieve the website title
title = driver.title

with open(os.getenv('GITHUB_ENV'), "a") as repo_env_file:
  repo_env_file.write(f"TITLE={title}\n")
  repo_env_file.write(f"URL={os.environ['URL']}\n")
  repo_env_file.write(f"LOGIN={os.environ['LOGIN']}\n")

# Close the webdriver
driver.quit()
