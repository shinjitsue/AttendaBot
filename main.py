import pickle
import cv2
import os
import cvzone
import face_recognition
import numpy as np

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
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
    'databaseURL': database_url,
    'storageBucket': storage_bucket
})
bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 630)
cap.set(4, 438)

imgBackground = cv2.imread('Resources/Background.png')

folderModePath = 'Resources/Models'
modePathList = os.listdir(folderModePath)
imgModeList = []

for path in modePathList:
    img = cv2.imread(os.path.join(folderModePath, path))
    if img is not None:
        imgModeList.append(img)

# Fixed coordinates (replace with your observed values)
top_left_y = 255
top_left_x = 79
webcam_height = 450
webcam_width = 639

# Load the encoding file
print("Loading Encoded File ..")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgStudent = []

target_height, target_width = 674, 463
target1_height, target1_width = 236, 233

# Ensure every image in imgModeList matches the target dimensions
for i in range(len(imgModeList)):
    if imgModeList[i].shape[:2] != (target_height, target_width):
        imgModeList[i] = cv2.resize(imgModeList[i], (target_width, target_height))

while True:
    success, img = cap.read()

    if not success:
        break

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    resized_img = cv2.resize(img, (webcam_width, webcam_height))

    # Embed using fixed coordinates
    imgBackground[top_left_y:top_left_y + webcam_height, top_left_x:top_left_x + webcam_width] = resized_img
    imgBackground[44:44 + target_height, 853:853 + target_width] = imgModeList[modeType]

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                id = studentIds[matchIndex]
                print(id)

                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading..", (275, 400))
                    cv2.imshow("AttendaBot", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

            if counter != 0:
                if counter == 1:
                    studentInfo = db.reference(f'Students/{id}').get()
                    print(studentInfo)
                    blob = bucket.get_blob(f'Image/{id}.jpg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    imgStudent = cv2.resize(imgStudent, (target1_width, target1_height))
                    # Update attendance
                    datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")

                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)
                    if secondsElapsed > 90:
                        ref = db.reference(f'Students/{id}')
                        studentInfo['total_attendance'] += 1
                        ref.child('total_attendance').set(studentInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + target_height, 853:853 + target_width] = imgModeList[modeType]

                if modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2

                        imgBackground[44:44 + target_height, 853:853 + target_width] = imgModeList[modeType]

                    if counter <=10:
                        cv2.putText(imgBackground, str(studentInfo['subject']), (1088, 555),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)

                        cv2.putText(imgBackground, str(studentInfo['section']), (1106, 629),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)

                        # Calculate the offset to center the name text
                        (w_name, h_name), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        name_offset = (463 - w_name) // 2

                        # Display the name with the calculated offset
                        cv2.putText(imgBackground, str(studentInfo['name']), (860 + name_offset, 485),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 1)

                        # Calculate the offset to center the ID text
                        (w_id, h_id), _ = cv2.getTextSize(str(id), cv2.FONT_HERSHEY_COMPLEX, 0.6, 2)
                        id_offset = (463 - w_id) // 2

                        # Display the ID with the calculated offset
                        cv2.putText(imgBackground, str(id), (855 + id_offset, 111),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 2)

                        imgBackground[182:182+target1_height, 968:968+target1_width] = imgStudent

                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        studentInfo = []
                        imgStudent = []
                        imgBackground[44:44 + target_height, 853:853 + target_width] = imgModeList[modeType]

    else:
        modeType = 0
        counter = 0

    cv2.imshow("AttendaBot", imgBackground)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()