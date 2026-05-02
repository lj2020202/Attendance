from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import base64
import os

app = Flask(__name__)

# Load known faces
known_encodings = []
known_names = []

def load_faces():
    global known_encodings, known_names
    
    folder = "known_faces"
    
    for file in os.listdir(folder):
        img = face_recognition.load_image_file(f"{folder}/{file}")
        encodings = face_recognition.face_encodings(img)
        
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(file.split(".")[0])

load_faces()

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json['image']
    
    # Decode base64 image
    img_data = base64.b64decode(data.split(",")[1])
    
    with open("temp.jpg", "wb") as f:
        f.write(img_data)
    
    unknown = face_recognition.load_image_file("temp.jpg")
    unknown_encodings = face_recognition.face_encodings(unknown)
    
    if not unknown_encodings:
        return jsonify({"status": "no_face"})
    
    for unknown_encoding in unknown_encodings:
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding)
        
        if True in matches:
            index = matches.index(True)
            name = known_names[index]
            
            return jsonify({
                "status": "matched",
                "name": name
            })
    
    return jsonify({"status": "not_found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
