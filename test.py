import base64
import firebase_admin
import json
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
  
private_key_str = os.environ['CDL_TEAM_KEY']
private_key = RSA.import_key(private_key_str)
encrypted_message = os.environ['ACTION']
cipher_rsa = PKCS1_OAEP.new(private_key)
message_bytes = base64.b64decode(encrypted_message)
decrypted_message = cipher_rsa.decrypt(message_bytes).decode()
json_string = decrypted_message.replace("'", '"')
json_object = json.loads(json_string)
output = f"Retrieved {json_object['firstName']} {json_object['lastName']} with coursesId {json_object['coursesId']}"

firebase_credentials = os.environ['FIREBASE_JSON']
firebase_creds_file = 'firebase-creds.json'
with open(firebase_creds_file, 'w') as file:
    file.write(firebase_credentials)
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()
doc_ref = db.collection('messages').document()
doc_ref.set({
    'message': output
})  

# Configure Chrome options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

# Initialize the Chrome webdriver with WebDriver Manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Navigate to the website URL
driver.get("https://github.com")

# Retrieve the website title
title = driver.title

with open(os.getenv('GITHUB_ENV'), "a") as repo_env_file:
  repo_env_file.write(f"TITLE={title}\n")
  repo_env_file.write(f"URL={os.environ['URL']}\n")
  repo_env_file.write(f"LOGIN={os.environ['LOGIN']}\n")

# Close the webdriver
driver.quit()
