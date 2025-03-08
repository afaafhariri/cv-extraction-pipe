from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit', methods=['POST'])
def submit_application():
   
    if 'cv' not in request.files:
        return jsonify({'error': 'No CV file provided'}), 400

    cv_file = request.files['cv']
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    if not name or not email or not phone:
        return jsonify({'error': 'Missing required fields'}), 400

    if cv_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if cv_file and allowed_file(cv_file.filename):
        filename = secure_filename(cv_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv_file.save(file_path)

        public_link = f"http://your-storage-service.com/{filename}"

        payload = {
            "cv_data": {
                "personal_info": {"name": name, "email": email, "phone": phone},
                "education": [],
                "qualifications": [],
                "projects": [],
                "cv_public_link": public_link,
            },
            "metadata": {
                "applicant_name": name,
                "email": email,
                "status": "testing",
                "cv_processed": True,
                "processed_timestamp": "2025-02-28T12:00:00Z"
            }
        }
        return jsonify(payload), 201

    else:
        return jsonify({'error': 'Invalid file type. Only PDF or DOCX allowed.'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
