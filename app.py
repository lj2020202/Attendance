from flask import Flask, request, jsonify
import face_recognition
import os
import base64

app = Flask(__name__)

known_encodings = []
known_names = []

# ---------------- LOAD FACES ----------------
def load_faces():
    global known_encodings, known_names

    known_encodings = []
    known_names = []

    folder = "known_faces"

    if not os.path.exists(folder):
        os.makedirs(folder)

    for file in os.listdir(folder):
        if file.endswith((".jpg", ".png", ".jpeg")):
            path = os.path.join(folder, file)

            try:
                img = face_recognition.load_image_file(path)
                enc = face_recognition.face_encodings(img)

                if enc:
                    known_encodings.append(enc[0])
                    known_names.append(file.split('.')[0])

            except:
                print("Bad image:", file)

load_faces()

# ---------------- VERIFY ----------------
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

            return jsonify({
                "status": "matched",
                "name": name
            })

    return jsonify({
        "status": "not_found"
    })

# ---------------- REGISTER ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    name = data['name']
    image_data = data['image']

    img_bytes = base64.b64decode(image_data.split(',')[1])

    folder = "known_faces"
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, f"{name}.jpg")

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    load_faces()

    return {
        "status": "success",
        "message": f"{name} registered"
    }

# ---------------- REGISTER PAGE ----------------
@app.route('/register-page')
def register_page():
    return open("register.html").read()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
