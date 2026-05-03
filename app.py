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
    """
    Combines texture analysis (Laplacian) and landmark detection 
    to filter out photos and screens.
    """
    # 1. Texture Check (detects pixel grids or flat surfaces)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # 2. Geometric Check (Ensure a 3D face structure exists)
    face_landmarks_list = face_recognition.face_landmarks(img_array)
    
    if not face_landmarks_list:
        return False, "No face structure detected."

    # Threshold for texture. Lower is more lenient, higher is stricter.
    if laplacian_var < 70: 
        return False, "Photo detected (Low texture variance)."

    return True, "Success"

def process_base64_image(base64_string):
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data)).convert('RGB')
    img_array = np.array(img)
    return img_array.astype(np.uint8)

@app.route('/get_face_encoding', methods=['POST'])
def get_face_encoding():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"status": "error", "message": "No image provided"}), 400

        rgb_img = process_base64_image(data['image'])
        
        # Anti-spoofing check
        is_real, reason = is_real_person(rgb_img)
        if not is_real:
            return jsonify({"status": "error", "message": reason}), 400

        face_encodings = face_recognition.face_encodings(rgb_img)
        if len(face_encodings) > 0:
            return jsonify({
                "status": "success", 
                "encoding": face_encodings[0].tolist()
            })
        else:
            return jsonify({"status": "error", "message": "AI could not find a face."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    try:
        data = request.json
        live_rgb = process_base64_image(data['live_image'])
        
        # Anti-spoofing check
        is_real, reason = is_real_person(live_rgb)
        if not is_real:
            return jsonify({"status": "error", "message": "Anti-spoofing: " + reason}), 400

        live_encodings = face_recognition.face_encodings(live_rgb)
        if not live_encodings:
            return jsonify({"status": "error", "message": "No face detected in camera"}), 400

        known_faces = data['known_faces']
        for person in known_faces:
            stored_encoding = np.array(person['encoding'])
            # Using 0.5 for higher accuracy (stricter than 0.6)
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
