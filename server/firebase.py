import firebase_admin
from firebase_admin import credentials, storage, firestore


cred = credentials.Certificate("/firebase-credentials.json ")


firebase_admin.initialize_app(cred, {
    'storageBucket': 'cv-extraction-84ef2.appspot.com'
})


db = firestore.client()