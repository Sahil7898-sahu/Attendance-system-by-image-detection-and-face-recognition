import face_recognition
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["shiksha_db"]
students_col = db["students"]

def register_student_multiple(student_data, img_paths):
    all_encodings = []
    for img_path in img_paths:
        img = face_recognition.load_image_file(img_path)
        encs = face_recognition.face_encodings(img)
        if encs: all_encodings.append(encs[0].tolist())
    
    if len(all_encodings) < 3: return "Failed: Need at least 3 clear face images."
    
    student_data["face_encodings"] = all_encodings
    students_col.insert_one(student_data)
    return f"Success: {student_data['name']} registered."