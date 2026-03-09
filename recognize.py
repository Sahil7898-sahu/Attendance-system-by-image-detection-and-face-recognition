import face_recognition
import cv2
import numpy as np
from datetime import datetime
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["shiksha_db"]
students_col = db["students"]
attendance_col = db["attendance_logs"]

def log_attendance(name):
    now = datetime.now()
    attendance_col.update_one(
        {"name": name, "date": now.strftime("%Y-%m-%d")},
        {"$set": {"time": now.strftime("%H:%M:%S"), "status": "Present"}},
        upsert=True
    )

def recognize_face_from_image(image_path):
    students = list(students_col.find())
    known_encs, known_names = [], []
    for s in students:
        for e in s["face_encodings"]:
            known_encs.append(np.array(e))
            known_names.append(s["name"])
    
    img = face_recognition.load_image_file(image_path)
    face_encs = face_recognition.face_encodings(img)
    matches_found = []
    for fe in face_encs:
        matches = face_recognition.compare_faces(known_encs, fe, tolerance=0.5)
        if True in matches:
            name = known_names[matches.index(True)]
            if name not in matches_found:
                matches_found.append(name)
                log_attendance(name)
    return matches_found

def recognize_face_from_camera():
    # Basic implementation: similar logic to image but using cv2.VideoCapture(0)
    # For this copy-paste, we assume the camera logic triggers and returns a list
    return ["Camera Mock User"]