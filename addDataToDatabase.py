import firebase_admin
import os
from firebase_admin import credentials
from firebase_admin import db
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')
database_url = os.getenv('DATABASE_URL')
storage_bucket = os.getenv('STORAGE_BUCKET')

# Initialize Firebase
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'databaseURL': database_url
})

ref = db.reference('Students')

data = {
    "201-00865":
        {
            "name": "Honey Mae Omela",
            "subject": "CSC 126",
            "section": "FG1",
            "last_attendance_time": "2024-05-15 13:50:00",
            "total_attendance": 1
        },
    "211-02152":
        {
            "name": "Joren Verdad",
            "subject": "CSC 123",
            "section": "JP1",
            "last_attendance_time": "2024-05-15 14:50:00",
            "total_attendance": 1
        },
    "211-00136":
        {
            "name": "Alexa Rae Flores",
            "subject": "CSC - 126",
            "section": "FG1",
            "last_attendance_time": "2024-05-15 14:50:00",
            "total_attendance": 1
        },
    "191-10871":
        {
            "name": "Dharelle Esmael",
            "subject": "CSC - 126",
            "section": "FG1",
            "last_attendance_time": "2024-05-15 14:50:00",
            "total_attendance": 1
        },
    "211-01581":
        {
            "name": "Jewel Mae Gepana",
            "subject": "CSC - 126",
            "section": "FG1",
            "last_attendance_time": "2024-05-15 14:50:00",
            "total_attendance": 1
        }
}

for key, value in data.items():
    ref.child(key).set(value)