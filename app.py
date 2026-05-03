from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import base64
import io
from PIL import Image

app = Flask(__name__)
CORS(app)

def process_base64_image(base64_string):
    # Remove the header (e.g., "data:image/jpeg;base64,")
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    # Decode base64 to bytes
    img_data = base64.b64decode(base64_string)
    
    # Open with PIL
    img = Image.open(io.BytesIO(img_data))
    
    # 1. Force convert to RGB (removes transparency/grayscale)
    img = img.convert('RGB')
    
    # 2. Convert to Numpy Array
    img_array = np.array(img)
    
    # 3. CRITICAL FIX: Force the array to be 8-bit unsigned integers
    # This specifically fixes the "Unsupported image type" error
    return img_array.astype(np.uint8)

@app.route('/get_face_encoding', methods=['POST'])
def get_face_encoding():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"status": "error", "message": "No image provided"}), 400

        rgb_img = process_base64_image(data['image'])
        
        # Detect faces
        face_encodings = face_recognition.face_encodings(rgb_img)

        if len(face_encodings) > 0:
            return jsonify({
                "status": "success", 
                "encoding": face_encodings[0].tolist()
            })
        else:
            return jsonify({"status": "error", "message": "AI could not find a face. Try better lighting."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    try:
        data = request.json
        live_rgb = process_base64_image(data['live_image'])
        live_encodings = face_recognition.face_encodings(live_rgb)
        
        if not live_encodings:
            return jsonify({"status": "error", "message": "No face detected in camera"}), 400

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
