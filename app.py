from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import base64
import cv2
import io
from PIL import Image

app = Flask(__name__)
CORS(app)

def process_base64_image(base64_string):
    # Remove the header if present (e.g., "data:image/jpeg;base64,")
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    # Decode base64 to bytes
    img_data = base64.b64decode(base64_string)
    
    # Use PIL to open the image - this handles many format issues automatically
    img = Image.open(io.BytesIO(img_data))
    
    # CRITICAL: Convert to RGB (removes Alpha channels or Grayscale issues)
    img = img.convert('RGB')
    
    # Convert back to a format OpenCV/Numpy can use
    return np.array(img)

@app.route('/get_face_encoding', methods=['POST'])
def get_face_encoding():
    try:
        data = request.json
        if 'image' not in data:
            return jsonify({"status": "error", "message": "No image provided"}), 400

        # Process and fix the image format
        rgb_img = process_base64_image(data['image'])
        
        # Detect faces
        face_encodings = face_recognition.face_encodings(rgb_img)

        if len(face_encodings) > 0:
            return jsonify({
                "status": "success", 
                "encoding": face_encodings[0].tolist()
            })
        else:
            return jsonify({"status": "error", "message": "No face detected. Please face the camera clearly."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    try:
        data = request.json
        if 'live_image' not in data or 'known_faces' not in data:
            return jsonify({"status": "error", "message": "Missing data"}), 400

        # Process live image
        live_rgb = process_base64_image(data['live_image'])
        live_encodings = face_recognition.face_encodings(live_rgb)
        
        if not live_encodings:
            return jsonify({"status": "error", "message": "No face in live photo"}), 400

        known_faces = data['known_faces']
        
        for person in known_faces:
            stored_encoding = np.array(person['encoding'])
            # Compare
            match = face_recognition.compare_faces([stored_encoding], live_encodings[0], tolerance=0.6)
            
            if match[0]:
                return jsonify({"status": "success", "match": person['name']})

        return jsonify({"status": "success", "match": None})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
