from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import base64
import cv2

app = Flask(__name__)
CORS(app)

# --- ROUTE 1: FOR REGISTRATION ---
@app.route('/get_face_encoding', methods=['POST'])
def get_face_encoding():
    try:
        data = request.json
        header, encoded = data['image'].split(",", 1)
        image_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        face_encodings = face_recognition.face_encodings(rgb_img)

        if len(face_encodings) > 0:
            return jsonify({"status": "success", "encoding": face_encodings[0].tolist()})
        return jsonify({"status": "error", "message": "No face detected"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ROUTE 2: FOR VERIFICATION (New!) ---
@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    try:
        data = request.json
        # 1. Decode the live photo from the webcam
        header, encoded = data['live_image'].split(",", 1)
        live_img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(live_img_bytes, np.uint8)
        live_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        live_rgb = cv2.cvtColor(live_img, cv2.COLOR_BGR2RGB)
        
        live_encoding = face_recognition.face_encodings(live_rgb)
        if not live_encoding:
            return jsonify({"status": "error", "message": "No face in live photo"}), 400

        # 2. Get the list of known faces sent from PHP
        known_faces = data['known_faces'] # List of { "name": "...", "encoding": [...] }
        
        for person in known_faces:
            stored_encoding = np.array(person['encoding'])
            # Compare live face to this stored face
            # tolerance 0.6 is standard; lower (0.4) is stricter
            match = face_recognition.compare_faces([stored_encoding], live_encoding[0], tolerance=0.6)
            
            if match[0]:
                return jsonify({"status": "success", "match": person['name']})

        return jsonify({"status": "success", "match": None}) # No match found
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
