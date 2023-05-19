import firebase_admin
import os
import sys
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
  
firebase_credentials = os.environ['FIREBASE_JSON']
firebase_creds_file = 'firebase-creds.json'
with open(firebase_creds_file, 'w') as file:
    file.write(firebase_credentials)
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()
doc_ref = db.collection('messages').document()
doc_ref.set({
    'message': 'test123'
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
