from flask import Flask, request, jsonify
import face_recognition
import os
import base64
import sqlite3
from datetime import datetime
from openpyxl import Workbook
from flask import request
import os
import base64
from flask import request

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

    # Get last record of this person
    c.execute("""
        SELECT * FROM attendance 
        WHERE name=? 
        ORDER BY id DESC 
        LIMIT 1
    """, (name,))

    last = c.fetchone()
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # -----------------------------
    # COOLDOWN CHECK (5 seconds)
    # -----------------------------
    if last:
        last_time = datetime.strptime(last[2], "%Y-%m-%d %H:%M:%S")
        diff = (now - last_time).seconds

        if diff < 5:
            conn.close()
            return "Already recorded (wait 5s)"

    # -----------------------------
    # IN / OUT LOGIC
    # -----------------------------
    if last is None or last[3] == "OUT":
        c.execute(
            "INSERT INTO attendance (name, time, type) VALUES (?, ?, ?)",
            (name, now_str, "IN")
        )
        conn.commit()
        conn.close()
        return "Time IN recorded"

    else:
        c.execute(
            "INSERT INTO attendance (name, time, type) VALUES (?, ?, ?)",
            (name, now_str, "OUT")
        )
        conn.commit()
        conn.close()
        return "Time OUT recorded"
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

@app.route('/export', methods=['GET'])
def export_excel():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("SELECT name, time, type FROM attendance")
    data = c.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    # Header
    ws.append(["Name", "Time", "Type"])

    # Data rows
    for row in data:
        ws.append(row)

    file_path = "attendance.xlsx"
    wb.save(file_path)

    return jsonify({
        "status": "success",
        "file": "/download"
    })
from flask import send_file

@app.route('/download', methods=['GET'])
def download():
    return send_file(
        "attendance.xlsx",
        as_attachment=True
    )

@app.route('/admin', methods=['GET'])
def admin():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("SELECT name, time, type FROM attendance ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 8px; }
            th { background: #333; color: white; }
        </style>
    </head>
    <body>
        <h2>Attendance Dashboard</h2>
        <a href="/export">Export Excel</a>
        <br><br>
        <table>
            <tr>
                <th>Name</th>
                <th>Time</th>
                <th>Type</th>
            </tr>
    """

    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>"

    html += """
        </table>
    </body>
    </html>
    """

    return html

@app.route('/register', methods=['POST'])
def register():
    data = request.json

    name = data['name']
    image_data = data['image']

    # Decode image
    img_bytes = base64.b64decode(image_data.split(',')[1])

    # Save into known_faces folder
    folder = "known_faces"
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, f"{name}.jpg")

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    # Reload faces
    global known_encodings, known_names
    known_encodings = []
    known_names = []
    load_faces()

    return {
        "status": "success",
        "message": f"{name} registered successfully"
    }

@app.route('/register-page')
def register_page():
    return """
    <html>
    <head>
        <title>Register Face</title>
        <style>
            body { font-family: Arial; text-align: center; }
            video, canvas { border: 1px solid black; }
            input, button { padding: 10px; margin: 10px; }
        </style>
    </head>
    <body>

        <h2>Face Registration</h2>

        <input type="text" id="name" placeholder="Enter name" /><br>

        <video id="video" width="300" height="220" autoplay></video><br>

        <button onclick="capture()">Capture & Register</button>

        <p id="result"></p>

        <canvas id="canvas" width="300" height="220" style="display:none;"></canvas>

        <script>
            const video = document.getElementById('video');

            // Access camera
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                });

            function capture() {
                const name = document.getElementById("name").value;

                if (!name) {
                    alert("Enter name first");
                    return;
                }

                const canvas = document.getElementById('canvas');
                const context = canvas.getContext('2d');

                context.drawImage(video, 0, 0, 300, 220);

                const image = canvas.toDataURL("image/jpeg");

                fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        image: image
                    })
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById("result").innerText = data.message;
                })
                .catch(err => {
                    document.getElementById("result").innerText = "Error registering";
                });
            }
        </script>

    </body>
    </html>
    """
