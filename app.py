from flask import Flask, request, jsonify
import face_recognition
import os
import base64
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ----------------------------
# LOAD FACES
# ----------------------------
known_encodings = []
known_names = []

def load_faces():
    folder = "known_faces"

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        try:
            img = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(img)

            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(file.split('.')[0])

        except Exception as e:
            print("Skip:", file, e)

load_faces()

# ----------------------------
# DATABASE SETUP
# ----------------------------
def init_db():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time TEXT,
            type TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ----------------------------
# ATTENDANCE LOGIC (IN / OUT)
# ----------------------------
def mark_attendance(name):
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
        SELECT * FROM attendance 
        WHERE name=? 
        ORDER BY id DESC LIMIT 1
    """, (name,))

    last = c.fetchone()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if last is None or last[3] == "OUT":
        c.execute("INSERT INTO attendance (name, time, type) VALUES (?, ?, ?)",
                  (name, now, "IN"))
        conn.commit()
        conn.close()
        return "Time IN recorded"

    else:
        c.execute("INSERT INTO attendance (name, time, type) VALUES (?, ?, ?)",
                  (name, now, "OUT"))
        conn.commit()
        conn.close()
        return "Time OUT recorded"
if last:
    last_time = datetime.strptime(last[2], "%Y-%m-%d %H:%M:%S")
    diff = (now_time - last_time).seconds

    if diff < 5:
        return "Already recorded (wait 5s)"
        

# ----------------------------
# API ROUTE
# ----------------------------
@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    image_data = data['image']

    img_bytes = base64.b64decode(image_data.split(',')[1])

    with open("temp.jpg", "wb") as f:
        f.write(img_bytes)

    unknown = face_recognition.load_image_file("temp.jpg")
    encodings = face_recognition.face_encodings(unknown)

    if not encodings:
        return jsonify({"status": "no_face"})

    for encoding in encodings:
        matches = face_recognition.compare_faces(known_encodings, encoding)

        if True in matches:
            index = matches.index(True)
            name = known_names[index]

            message = mark_attendance(name)

            return jsonify({
                "status": "matched",
                "name": name,
                "message": message
            })

    return jsonify({
        "status": "not_found",
        "message": "Face not found in database"
    })

# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
