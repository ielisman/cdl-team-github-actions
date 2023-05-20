import argparse
import base64
import keller_constants as const
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

# only when script runs with --enroll option, only than it will actuall enroll student to avoid charges
parser = argparse.ArgumentParser(description ='Keller Automation Script')
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
email = json_object['email']
id = json_object['id']
coursesId = json_object['coursesId']
phone = json_object['phone']

# selenium run
def addStudent(firstName,lastName,email,phone,id,location) -> bool:
    print(f"Adding student {id} {firstName} {lastName} {email} {phone}")
    flag = False
    try:
        aAddStudentRec = driver.find_element(by=By.LINK_TEXT, value=const.STUDENT_PAGE_ATXT_ADDSTUDREC)
        aAddStudentRec.click()
    except:
        raise WebDriverException("Add Student: unable to click Add Student Record") 

    try:
        WebDriverWait(driver, 15).until(
            EC.text_to_be_present_in_element_attribute(
                (By.ID, const.ADDSTUD_PAGE_ID_EMAIL), 
                const.ADDSTUD_PAGE_ID_EMAIL_TYPE, 
                const.ADDSTUD_PAGE_ID_EMAIL_VAL)
        )
    except:
        print(f"Add Student: waiting to get add students record page failed")        

    try:
        txtStudentFname = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_FIRSTNAME)
        txtStudentLname = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_LASTNAME)
        selStudentLocat = Select(driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_LOCATION))
        txtStudentEmail = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_EMAIL)
        txtStudentPhone = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_PHONE)
        txtStudentLicId = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_ID)
        btnStudentSave  = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_BTN_SAVE)

        txtStudentFname.send_keys(firstName)
        txtStudentLname.send_keys(lastName)
        txtStudentEmail.send_keys(email)
        txtStudentPhone.send_keys(phone)
        txtStudentLicId.send_keys(id)
        selStudentLocat.select_by_value(location) # selStudentLocat.select_by_visible_text('Red Hook Commercial Driving School')
        btnStudentSave.click()
        flag = True
    except:
        raise WebDriverException("Add Student: unable to Add Student Record") 
    finally:
        clearAddStudentRecordFields()

    return flag

def clearAddStudentRecordFields():
    try:                        
        txtStudentFname = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_FIRSTNAME)
        txtStudentLname = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_LASTNAME)                
        txtStudentEmail = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_EMAIL)
        txtStudentPhone = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_PHONE) 
        txtStudentLicId = driver.find_element(by=By.ID, value=const.ADDSTUD_PAGE_ID_ID)               

        txtStudentFname.clear()
        txtStudentLname.clear()
        txtStudentEmail.clear()
        txtStudentPhone.clear()
        txtStudentLicId.clear()
    except:
        pass

def is_element_present(by, value):
    try: driver.find_element(by=by, value=value)
    except NoSuchElementException as e: return False
    return True

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

if not args.enroll:
    print("Dry run: will not enroll student")

# LOGIN
driver.get(const.KELLER_URL)
driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_EMAIL).clear()
driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_EMAIL).send_keys(const.LOGIN_PAGE_VAL_EMAIL)
driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_PASSWORD).clear()
driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_PASSWORD).send_keys(const.LOGIN_PAGE_VAL_PASSWORD)  
driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_SIGNIN).click()

# DASHBOARD - verify if logged in
try:
    signout = driver.find_element(by=By.ID, value=const.DASH_PAGE_ID_SIGNOUT)
    if (signout.text != const.DASH_PAGE_VAL_SIGNOUT):
        print ("Login error: Do not see sign out in Dashboard")
        doc_ref = db.collection('messages').document()
        doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Login error: Do not see sign out in Dashboard. Student {firstName} {lastName}" })
        quit()
except:
    print ("Login error: cannot login")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Login error: cannot login. Student {firstName} {lastName}" })
    quit()

# STUDENTS PAGE
aMyStudents = driver.find_element(by=By.LINK_TEXT, value=const.DASH_PAGE_ATXT_MYSTUDENTS)
aMyStudents.click()
try:
    searchBtn = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_SEARCH)
    searchBtnType = searchBtn.get_attribute(const.STUDENT_PAGE_ATT_TP_SEARCH)
    if searchBtnType != const.STUDENT_PAGE_ATT_VAL_SEARCH:
        print (f"Students error: Do not see {const.STUDENT_PAGE_ATT_TP_SEARCH}={const.STUDENT_PAGE_ATT_VAL_SEARCH} in {const.STUDENT_PAGE_ID_SEARCH}")
        doc_ref = db.collection('messages').document()
        doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Students error: Do not see {const.STUDENT_PAGE_ATT_TP_SEARCH}={const.STUDENT_PAGE_ATT_VAL_SEARCH} in {const.STUDENT_PAGE_ID_SEARCH}. Student {firstName} {lastName}" })
        quit()
except:
    print ("Students error: cannot find student page elements")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Students error: cannot find student page elements. Student {firstName} {lastName}" })
    quit()

# SEARCH FOR SPECIFIC STUDENT  
txtId = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_ID)
txtId.clear()
txtId.send_keys(id)
try:
    grid = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_GRID)
    searchBtn = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_SEARCH)            
    searchBtn.click()            
    WebDriverWait(driver, 20).until(EC.staleness_of(grid))
except:
    print(f"Search Student: unable to submit user search for {id}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Search Student: unable to submit user search for {firstName} {lastName}" })
    quit()
    
# SEE IF ANY RECORDS RETURNED PER STUDENT
isStudentRegistered = False
try: # only parsing first 50 records
    totalStudentsFound = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_STUD_COUNT)
    count = int(totalStudentsFound.text)
    if count != 0:
        isStudentRegistered = True
        print (f"Found id {id}")
except:
    print(f"Search Student Record: unable to retrieve user search for {id}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Search Student Record: unable to retrieve user search for {firstName} {lastName}" })
    quit()

# STUDENT IS NOT FOUND, REGISTER THAT STUDENT
if not isStudentRegistered:
    print(f"Registering student with id {id}")
    try:
        result = addStudent(firstName=firstName, lastName=lastName, email=email, phone=phone, id=id, location=const.DEFAULT_LOCATION)
        if not result:
             print (f"Save Student Record: Problem saving student with id {id}")
             doc_ref = db.collection('messages').document()
             doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Save Student Record: Unable to save student {firstName} {lastName}" })
             quit()
        else:
            driver.get(const.DASH_URL)
    except:
        print (f"Save Student Record: Unable to save student with id {id}")
        doc_ref = db.collection('messages').document()
        doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Save Student Record: Unable to save student {firstName} {lastName}" })
        quit()
else:
    print (f"student with id {id} is already registered in the system")

WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.ID, const.DASH_PAGE_ID_ONLINETRAINING) ))

# OPEN COURSES PAGE, SELECT A COURSE, SEARCH, FIND AND SELECT STUDENT TO ENROLL
driver.get(f"{const.ENROLL_PAGE_CURRICULUM_URL_PRE}{coursesId}")
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_ENROLL_STUDENTS).click()
driver.get(f"{const.ENROLL_PAGE_STENRBATCH_URL_PRE}{coursesId}")
WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.ID, const.ENROLL_PAGE_ID_PAGER_SEARCH) ))
dataPage = driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_PAGER_SEARCH)
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_LAST_NAME).clear()
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_LAST_NAME).send_keys(lastName)
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_SEARCH).click()
WebDriverWait(driver, 20).until(EC.staleness_of(dataPage))
trList = driver.find_elements(by=By.XPATH, value=const.ENROLL_PAGE_TBL_SEARCH_RES)
i=0
flagEnroll = False
for tr in trList:
    if i>0:
        if (tr.text != const.ENROLL_PAGE_TBL_NOT_FOUND):
            recIndex = i-1
            recId = tr.find_element(by=By.ID, value=f"{const.ENROLL_PAGE_TBL_STUDID_PRE}{recIndex}")
            if recId.text == id:
                flagEnroll = True
                selectRec = tr.find_element(by=By.ID, value=f"{const.ENROLL_PAGE_TBL_STUDSEL_PRE}{recIndex}")
                selectRec.click()
    i = i + 1
if not flagEnroll:
    print (f"Cannot select record for id {id}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Cannot select record for {firstName} {lastName}" })
    quit()

# SET 80 SCORE
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_CONTINUE).click()
WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.ID, const.ENROLL_PAGE_ID_CHECKALL) ))
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_CHECKALL).click()
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_CONTINUE2).click()
WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.ID, const.ENROLL_PAGE_ID_SEL_SCORE) ))
Select(driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_SEL_SCORE)).select_by_visible_text(const.ENROLL_PAGE_VAL_SEL_SCORE)
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_APPLY).click()
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_CONTINUE3).click()

driver.implicitly_wait(10)

# SET DUE DATES, CONFIRM SELECTION AND ENROLL STUDENT
expirationDate = date.today() + timedelta(days=const.ENROLL_PAGE_EXPIRATION_DAYS)
remindDate = expirationDate -  timedelta(days=const.ENROLL_PAGE_REMIND_BEFORE_EXP)
strExpirationDate = expirationDate.strftime(const.ENROLL_PAGE_DATE_FORMAT)
strRemindDate = remindDate.strftime(const.ENROLL_PAGE_DATE_FORMAT)
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_REMINDER).clear()
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_REMINDER).send_keys(strRemindDate)
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_EXPIRATION).clear()
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_EXPIRATION).send_keys(strExpirationDate)
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_CONTINUE4).click()
driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_CONTINUE5).click()
if (args.enroll):
  driver.find_element(by=By.ID, value=const.ENROLL_PAGE_ID_COMPLETE_ENROLL).click()

# VERIFY THAT STUDENT IS ACTUALLY ENROLLED
driver.get(const.VERIFY_PAGE_STUDENTS_PAGE)
txtId = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_ID)
txtId.clear()
txtId.send_keys(id)
try:
    grid = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_GRID)
    searchBtn = driver.find_element(by=By.ID, value=const.STUDENT_PAGE_ID_SEARCH)            
    searchBtn.click()            
    WebDriverWait(driver, 20).until(EC.staleness_of(grid))    
except:
    print(f"Search Student: unable to submit user search for {id}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Search Student: unable to submit user search for {firstName} {lastName}" })
    quit()

if not is_element_present(by=By.ID, value=const.VERIFY_PAGE_ID_RECORD_ONE):
    print (f"Verify student enrollement: cannot find student with id {id}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Verify student enrollement: cannot find student with id {firstName} {lastName}" })
    quit()
driver.find_element(by=By.ID, value=const.VERIFY_PAGE_ID_RECORD_ONE).click()
if not is_element_present(by=By.ID, value=const.VERIFY_PAGE_ID_REC_37):
    print (f"Could not find enrollement for student id {id}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Not enrolled', 'createdOn': datetime.now(), 'message': f"Could not find enrollement for student id {firstName} {lastName}" })
    quit()
else:
    print(f"Student {firstName} {lastName} with id {id} is enrolled into {coursesId}")
    doc_ref = db.collection('messages').document()
    doc_ref.set({ 'studentId': id, 'coursesId': coursesId, 'status': 'Enrolled', 'createdOn': datetime.now(), 'message':'Success' })

#time.sleep(30)
#title = driver.title
#print("Enroll was simulated")
#print(title)

driver.quit()
