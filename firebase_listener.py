import argparse
import base64
import firebase_admin
import json
import os
import time

from datetime                           import timedelta, date, datetime
from firebase_admin                     import credentials, firestore

# set up firebase store
firebase_credentials = os.environ['FIREBASE_JSON']
firebase_creds_file = 'firebase-creds.json'
with open(firebase_creds_file, 'w') as file:
    file.write(firebase_credentials)
cred = credentials.Certificate(firebase_creds_file)
firebase_admin.initialize_app(cred)
db = firestore.client()

schedule_collection = db.collection('schedule')
logging_collection = db.collection('logging')

def on_snapshot(docs, changes, read_time):
    for change in changes:
        if change.type.name == 'REMOVED':
            log_deletion('schedule', 'remove', change.document.id, change.document.to_dict())

def log_deletion(fs_col, fs_type, doc_id, doc_data):
    log_entry = {
        'coll': fs_col,
        'date': firestore.SERVER_TIMESTAMP,
        'type': fs_type,
        'doc_id': doc_id,
        'value': doc_data        
    }
    logging_collection.add(log_entry)
    print(f"Logged deletion of document {doc_id}")

def main():
    print("Listening for deletions in 'schedule' collection...")
    query_watch = schedule_collection.on_snapshot(on_snapshot)

    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        query_watch.unsubscribe()
        print("Stopped listening for deletions.")

if __name__ == "__main__":
    main()
