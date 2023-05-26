import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

school = '37003007'
sid    = 'NY-123456789'
id     = '123456789'
cid    = '10840'
tm     = datetime.now()

new_record = {
    'created_on': tm,
    'message': 'New message again',
    'status': 'Pending'
}

firebase_creds_file = 'c:\\temp\\firebase_creds.json'
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()
doc_ref = db.collection('integrations').document(school).collection('jjkeller').document(sid)

doc = doc_ref.get()
if doc.exists:
    existing_data = doc.to_dict()
    if cid in existing_data['courses']:
        existing_data['courses'][cid].insert(0, new_record)
    else:
        existing_data['courses'][cid] = [new_record]
    doc_ref.update({'courses': existing_data['courses']})
else:
    new_data = {
    'courses': {
        cid: [
                {
                    'created_on': tm,
                    'message': 'Sample message 1',
                    'status': 'Completed'
                },
            ]
        }
    }
    doc_ref.set(new_data)

#the_doc.set({ 'studentId': id, 'coursesId': coursesId, 'status': status, 'createdOn': createdOn, 'message': message })
#writeToFirestore('Enrolled',f"Student Igor Elisman with id NY-666721074 successfully enrolled into 10839")

