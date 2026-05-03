from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import base64
import cv2

app = Flask(__name__)
# CORS allows your InfinityFree website to talk to this Railway script
CORS(app)

@app.route('/get_face_encoding', methods=['POST'])
def get_face_encoding():
    try:
        # Get the JSON data sent from the browser
        data = request.json
        if 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400

        # The image comes as a Base64 string (data:image/jpeg;base64,...)
        # We need to strip the header and decode it
        header, encoded = data['image'].split(",", 1)
        image_bytes = base64.b64decode(encoded)
        
        # Convert bytes to an OpenCV image format
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect faces and get encodings (the "fingerprint" of the face)
        face_encodings = face_recognition.face_encodings(rgb_img)

        if len(face_encodings) > 0:
            # We take the first face detected and convert the numpy array to a standard list
            encoding_list = face_encodings[0].tolist()
            return jsonify({
                "status": "success",
                "encoding": encoding_list
            })
        else:
            return jsonify({"status": "error", "message": "No face detected in the image"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Railway provides a port via environment variables
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
