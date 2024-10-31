import firebase_admin
import json
import os
import time

from datetime                           import timedelta, date, datetime
from firebase_admin                     import credentials, firestore
from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

def is_element_present(by, value):
    try: driver.find_element(by=by, value=value)
    except NoSuchElementException as e: return False
    return True

# set up firebase store
firebase_credentials = os.environ['FIREBASE_JSON']
school_id = os.environ['SCHOOL_ID']
firebase_creds_file = 'firebase-creds.json'
with open(firebase_creds_file, 'w') as file:
    file.write(firebase_credentials)
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()
schedule_ref = db.collection('schedule')
students_ref = db.collection('students').document(school_id).collection('records')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
  license_list = []
  student_schedule_map = {}
  today = date.today()
  start_timestamp = datetime.combine(today, datetime.time.min)
  end_timestamp = datetime.combine(today, datetime.time.max)
  schedule_query = schedule_ref.where('event_type', '==', 'Road Test').where('event_from', '>=', start_timestamp).where('event_from', '<=', end_timestamp).stream()
  for doc in schedule_query:
    doc_data = doc.to_dict()
    student_id = doc_data['student_license_number']
    license_list.append(student_id)
    student_schedule_map[student_id] = doc.id
  if (len(license_list) != 0):
    students_query = students_ref.where('license_number', 'in', license_list).stream()
    for student_doc in students_query:
      student_data = student_doc.to_dict()
      id = student_data['license_number']
      dob = student_data['dob']
      driver.get(os.environ['ROAD_TEST_URL'])
      driver.find_element(by=By.ID, value="input-57").clear()
      driver.find_element(by=By.ID, value="input-57").send_keys(id)
      driver.find_element(by=By.ID, value="input-61").clear()
      driver.find_element(by=By.ID, value="input-61").send_keys(dob)
      driver.find_element(by=By.XPATH, value="//div[@id='app']/div/main/div/div[2]/div/form/div/div[4]/button/span").click()
      # here retrieve date from web page (and RT class, i.e. Class A), if date matches today,
      result = "Passed"
      if (1==2):
        driver.find_element(by=By.XPATH, value="//div[@id='app']/div/main/div/div[2]/div/div/div[2]/div/div/div/table/tbody/tr[2]/td[5]/span/a").click()
        # parse results
        if student_schedule_map[id] is not None:
          doc_ref = schedule_ref.document(student_schedule_map[id])
          doc = doc_ref.get()
          if doc.exists:
            data = doc.to_dict()
            if result == "Failed":
              doc_ref.update({'event_status': result, school_notes: f"{data['school_notes']}. Failed Road part" })
            else:
              doc_ref.update({'event_status': result})

except Exception as e:
  print(f"Exception occurred when getting road test results: {e}")
