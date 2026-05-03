from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import base64
import io
import cv2
from PIL import Image

app = Flask(__name__)
CORS(app)

def is_real_person(img_array):
    # Liveness check: Laplacian variance
    # Real faces have a specific range of texture. 
    # Photos/Screens are often too sharp or too blurry.
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    # If score is very low, it's likely a flat screen/photo
    if score < 50: 
        return False
    return True

def process_base64_image(base64_string):
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data)).convert('RGB')
    return np.array(img).astype(np.uint8)

@app.route('/get_face_encoding', methods=['POST'])
def get_face_encoding():
    try:
        data = request.json
        rgb_img = process_base64_image(data['image'])
        
        if not is_real_person(rgb_img):
            return jsonify({"status": "error", "message": "Liveness check failed. Use a real face, not a photo."}), 400

        face_encodings = face_recognition.face_encodings(rgb_img)
        if len(face_encodings) > 0:
            return jsonify({"status": "success", "encoding": face_encodings[0].tolist()})
        return jsonify({"status": "error", "message": "No face detected."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    try:
        data = request.json
        live_rgb = process_base64_image(data['live_image'])
        
        if not is_real_person(live_rgb):
            return jsonify({"status": "error", "message": "Anti-Spoofing: Photo detected!"}), 400

        live_encodings = face_recognition.face_encodings(live_rgb)
        if not live_encodings:
            return jsonify({"status": "error", "message": "No face detected"}), 400

        known_faces = data['known_faces']
        for person in known_faces:
            stored_encoding = np.array(person['encoding'])
            match = face_recognition.compare_faces([stored_encoding], live_encodings[0], tolerance=0.5)
            if match[0]:
                return jsonify({"status": "success", "match": person['name']})

        return jsonify({"status": "success", "match": None})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
