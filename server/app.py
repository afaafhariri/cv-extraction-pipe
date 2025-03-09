import os
import datetime
import uuid
import requests
import pdfplumber

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from docx import Document

from firebase import bucket

# --------------------- Google Sheets Setup ----------------------
import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "google-sheets.json" 
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
gs_creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(gs_creds)

SHEET_ID = "1UUK23iOdUwecTdXMwMiHqeZj9ooDh8Rs9jP9QnGSdCw"
sheet = gc.open_by_key(SHEET_ID).sheet1


# --------------------- Firebase Setup ----------------------------
app = Flask(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------- CV Parsing Functions ---------------------
def parse_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def parse_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_sections(full_text):
    """
    Placeholder extraction logic.
    Replace with actual logic for Education, Qualifications, and Projects.
    """
    return {
        "education": ["Bachelor of Science in Something"],
        "qualifications": ["Sample Qualification"],
        "projects": ["Sample Project"],
    }

# --------------------- Upload to Firebase -------------------------
def upload_file_to_firebase(local_path, filename):
    unique_name = str(uuid.uuid4()) + "_" + filename
    blob = bucket.blob(unique_name)
    blob.upload_from_filename(local_path)
    blob.make_public()  # Make file publicly accessible
    return blob.public_url

# --------------------- Write to Google Sheets ---------------------
def write_to_google_sheet(row_data):
    sheet.append_row(row_data)

# --------------------- Webhook Notification -----------------------
def send_webhook_notification(payload):
    webhook_url = "https://rnd-assignment.automations-3d6.workers.dev/"
    headers = {
        "Content-Type": "application/json",
        "X-Candidate-Email": "haririafaaf@gmail.com"  
    }
    response = requests.post(webhook_url, json=payload, headers=headers)
    return response.status_code

# --------------------- Flask API Endpoint -------------------------
@app.route("/submit", methods=["POST"])
def submit_cv():
    if "cv" not in request.files:
        return jsonify({"error": "No CV file provided"}), 400

    cv_file = request.files["cv"]
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")

    if not all([name, email, phone]):
        return jsonify({"error": "Missing required fields"}), 400

    if cv_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if cv_file and allowed_file(cv_file.filename):
        filename = secure_filename(cv_file.filename)
        os.makedirs("temp_uploads", exist_ok=True)
        local_path = os.path.join("temp_uploads", filename)
        cv_file.save(local_path)
       
        public_url = upload_file_to_firebase(local_path, filename)

        file_ext = filename.rsplit(".", 1)[1].lower()
        if file_ext == "pdf":
            full_text = parse_pdf(local_path)
        else:
            full_text = parse_docx(local_path)

        sections = extract_sections(full_text)

        cv_data = {
            "personal_info": {"name": name, "email": email, "phone": phone},
            "education": sections["education"],
            "qualifications": sections["qualifications"],
            "projects": sections["projects"],
            "cv_public_link": public_url
        }

        write_to_google_sheet([
            name,
            email,
            phone,
            public_url,
            ", ".join(sections["education"]),
            ", ".join(sections["qualifications"]),
            ", ".join(sections["projects"])
        ])

        payload = {
            "cv_data": cv_data,
            "metadata": {
                "applicant_name": name,
                "email": email,
                "status": "testing",  
                "cv_processed": True,
                "processed_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }

        send_webhook_notification(payload)

        return jsonify(payload), 201

    else:
        return jsonify({"error": "Invalid file type. Only PDF or DOCX allowed."}), 400

if __name__ == "__main__":
    os.makedirs("temp_uploads", exist_ok=True)
    app.run(debug=True, port=5000)
