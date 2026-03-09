from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from recognize import recognize_face_from_image, recognize_face_from_camera
from encode import register_student_multiple

app = Flask(__name__)
app.secret_key = "shiksha_super_secret_key"

# Database Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["shiksha_db"]
principal_col = db["principals"]
teacher_col = db["teachers"]
students_col = db["students"]
attendance_col = db["attendance_logs"]

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/')
def index():
    if "user_email" in session:
        return redirect(url_for("dashboard") if session['user_role'] == 'teacher' else url_for('principal_dashboard'))
    return render_template('login.html')

@app.route('/teacher-register')
def teacher_reg_page():
    return render_template('teacher-register.html')

@app.route('/principal-register')
def principal_reg_page():
    return render_template('principal-register.html')

@app.route('/api/register/teacher', methods=['POST'])
def register_teacher():
    data = request.form
    if teacher_col.find_one({"email": data.get('email')}):
        return "Email already registered", 400
    hashed_pw = generate_password_hash(data.get('password'))
    teacher_col.insert_one({
        "role": "teacher", "instituteCode": data.get('instituteCode'),
        "teacherName": data.get('teacherName'), "email": data.get('email'),
        "contact": data.get('contact'), "class_id": data.get('class_id'),
        "password": hashed_pw
    })
    return "success"

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = (principal_col if data.get('role') == "principal" else teacher_col).find_one({"email": data.get('email')})
    if user and check_password_hash(user['password'], data.get('password')):
        session.update({"user_email": user["email"], "user_role": data.get('role'), "user_name": user.get("principalName") or user.get("teacherName")})
        return jsonify({"status": "success", "role": data.get('role')})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session: return redirect(url_for("index"))
    records = list(attendance_col.find().sort([("date", -1), ("time", -1)]))
    return render_template("dashboard.html", records=records)

@app.route("/principal-dashboard")
def principal_dashboard():
    if "user_email" not in session: return redirect(url_for("index"))
    return "<h1>Principal Dashboard</h1><p>Welcome " + session['user_name'] + "</p><a href='/logout'>Logout</a>"

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if "user_email" not in session: return redirect(url_for("index"))
    matched_names = []
    if request.method == "POST":
        if "upload_image" in request.files and request.files["upload_image"].filename != '':
            file = request.files["upload_image"]
            path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(path)
            matched_names = recognize_face_from_image(path)
        elif "camera" in request.form:
            matched_names = recognize_face_from_camera()
    return render_template("attendance.html", matched_names=matched_names)

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_email" not in session: return redirect(url_for("index"))
    if request.method == "POST":
        files = request.files.getlist("images")
        paths = []
        for file in files:
            path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(path)
            paths.append(path)
        msg = register_student_multiple(request.form.to_dict(), paths)
        flash(msg)
        return redirect(url_for("register"))
    return render_template("register.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)