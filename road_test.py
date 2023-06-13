import argparse
import base64
import road_test_constants as const
import firebase_admin
import json
import os
import time

from Crypto.PublicKey                   import RSA
from Crypto.Cipher                      import PKCS1_OAEP
from datetime                           import timedelta, date, datetime
from firebase_admin                     import credentials, firestore
from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

parser = argparse.ArgumentParser(description ='Road Test Automation Script')
parser.add_argument('-e', '--enroll', dest = 'enroll', action='store_true', help='Enroll')
args = parser.parse_args()

# set up firebase store
firebase_credentials = os.environ['FIREBASE_JSON']
firebase_creds_file = 'firebase-creds.json'
with open(firebase_creds_file, 'w') as file:
    file.write(firebase_credentials)
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()

# probably don't need this except may be school id
# get message from app, decrypt it and convert to json
private_key_str = os.environ['CDL_TEAM_KEY']
private_key = RSA.import_key(private_key_str)
encrypted_message = os.environ['ACTION']
cipher_rsa = PKCS1_OAEP.new(private_key)
message_bytes = base64.b64decode(encrypted_message)
decrypted_message = cipher_rsa.decrypt(message_bytes).decode()
json_string = decrypted_message.replace("'", '"')
json_object = json.loads(json_string)

# get parameters from json
firstName = json_object['firstName']
lastName = json_object['lastName']
fln = f"{firstName} {lastName}"
email = json_object['email']
state_id = json_object['id']
try:
    id = state_id[state_id.index('-') + 1:]
except ValueError:
    id = state_id
dob = json_object['dob']
phone = json_object['phone']
pref = json_object['pref'] # 10+;ALL or 10-20;N|U|B i.e. 10+ days from today and ALL loc; 10-20 days from today, Nassau, Uniondale and Bellerose
schoolId = json_object['schoolId']

# script will listen for new users from firebase firestore and their road test preferences
# book, cancel, rebook (canc/book)
# If manual booking is detected, workflow should stop.
# If phone booking was used, we will run report every X minutes. Updates should be picked up into firebase
# schedule must be verified if there are no lessons at that date. 
# Send report if lessons can be moved or not
# you must ensure at least 2 road test for that day must be available for specific truck type.

doc_ref = db.collection('integrations').document(schoolId).collection('nyakts').document(state_id)

def writeToFirestore(status, message, test_date, test_time, action, doc_ref=doc_ref, state_id=state_id, id=id, email=email, phone=phone, createdOn=datetime.now(), isQuit=False):
    print(message)
    new_record = {
        'created_on': createdOn,
        'message': message,
        'status': status,
        'road_test_action': action, # add, cancel
        'road_test_date': test_date,
        'road_test_time': test_time,
    }
    doc = doc_ref.get()
    if doc.exists:
        existing_data = doc.to_dict()
        existing_data['road_tests'].insert(0, new_record)
        doc_ref.update({'road_tests': existing_data['road_tests']})
    else:
        new_data = { 'studentId': id, 'road_tests': [ new_record ] }
        doc_ref.set(new_data)

    if isQuit:
        quit()

def is_element_present(by, value):
    try: driver.find_element(by=by, value=value)
    except NoSuchElementException as e: return False
    return True

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

if not args.enroll:
    print("Dry run: will not register student for road test")

try:
    driver.get(const.ROAD_TEST_URL)
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_USERNAME).clear()
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_USERNAME).send_keys(os.environ['NYAKTS_USERNAME'])
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_PASSWORD).clear()
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_PASSWORD).send_keys(os.environ['NYAKTS_PASSWORD'])  
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_LOGIN).click()
    if is_element_present(by=By.ID, value=const.LOGIN_PAGE_ID_CONFIRM):
        driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_CONFIRM).click()

    # probably here try loop with N minutes frames, i.e. 5 min frame. Verification can run at any time during the frame.
    # wait for time frame to end. When new frame starts, repeat the process.
    # depending on time of the day, frame can decrease or increase in size.

except Exception as e:
    writeToFirestore('Not Registered',f"Exception occurred when registering {fln}: {e}", isQuit=True) 