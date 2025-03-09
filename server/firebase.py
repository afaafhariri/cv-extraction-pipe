import firebase_admin
from firebase_admin import credentials, storage
import os

FIREBASE_CRED_FILE = os.path.join(os.getcwd(), "firebase.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_FILE)
    firebase_admin.initialize_app(cred, {
        "storageBucket": "cv-extraction-84ef2.appspot.com"  
    })

bucket = storage.bucket()
#I guess this works
