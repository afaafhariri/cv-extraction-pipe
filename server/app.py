import os
import datetime
import uuid
import requests
import pdfplumber
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from docx import Document
import boto3
import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import atexit
import threading  # For asynchronous webhook calls

# --------------------- AWS S3 Setup ---------------------
S3_BUCKET = os.environ.get("S3_BUCKET", "cvextractionbucket")
s3_client = boto3.client('s3')

# --------------------- Google Sheets Setup ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "google-sheets.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
gs_creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(gs_creds)

SHEET_ID = "1UUK23iOdUwecTdXMwMiHqeZj9ooDh8Rs9jP9QnGSdCw"
sheet = gc.open_by_key(SHEET_ID).sheet1

# --------------------- Flask App Setup ----------------------------
app = Flask(__name__)
CORS(app)

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
    Replace with actual logic for:
    - Education
    - Qualifications
    - Projects
    - Personal Info (Name, Contact Details, etc.)
    """
    return {
        "education": ["Bachelor of Science in Something"],
        "qualifications": ["Sample Qualification"],
        "projects": ["Sample Project"],
    }

# --------------------- Upload to AWS S3 -------------------------
def upload_file_to_s3(local_path, filename):
    unique_filename = str(uuid.uuid4()) + "_" + filename
    try:
        s3_client.upload_file(local_path, S3_BUCKET, unique_filename)
        public_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{unique_filename}"
        return public_url
    except Exception as e:
        print("Error uploading file to S3:", e)
        return None

# --------------------- Write to Google Sheets ---------------------
def write_to_google_sheet(row_data):
    sheet.append_row(row_data)

# --------------------- Webhook Notification -----------------------
def send_webhook_notification(payload):
    """
    Sends an HTTP POST request to the given endpoint with the CV payload.
    Uses a timeout to avoid blocking indefinitely.
    """
    webhook_url = "https://rnd-assignment.automations-3d6.workers.dev/"
    headers = {
        "Content-Type": "application/json",
        "X-Candidate-Email": "haririafaaf@gmail.com"  # Replace if necessary.
    }
    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=5)
        print("Webhook response:", response.status_code)
    except requests.exceptions.Timeout:
        print("Webhook request timed out.")
    except Exception as e:
        print("Error sending webhook notification:", e)

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
       
        public_url = upload_file_to_s3(local_path, filename)
        if not public_url:
            return jsonify({"error": "File upload failed"}), 500

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

        # Write the CV data to Google Sheets
        write_to_google_sheet([
            name,
            email,
            phone,
            public_url,
            ", ".join(sections["education"]),
            ", ".join(sections["qualifications"]),
            ", ".join(sections["projects"])
        ])

        # Prepare the webhook payload.
        payload = {
            "cv_data": cv_data,
            "metadata": {
                "applicant_name": name,
                "email": email,
                "status": "testing",  # Use "prod" for a final submission.
                "cv_processed": True,
                "processed_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }

        # Send the webhook notification asynchronously.
        threading.Thread(target=send_webhook_notification, args=(payload,)).start()

        return jsonify(payload), 201

    else:
        return jsonify({"error": "Invalid file type. Only PDF or DOCX allowed."}), 400

# --------------------- Email Scheduling using APScheduler ---------------------
load_dotenv()

def send_followup_emails():
    try:
        emails = sheet.col_values(2)[1:]  # Skip header row if present
    except Exception as e:
        print("Error retrieving emails from Google Sheets:", e)
        return

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")

    subject = "Your CV is under review"
    body = (
        "Hello,\n\n"
        "Thank you for submitting your CV. Your application is under review, "
        "and we will update you shortly.\n\n"
        "Best regards,\nThe Team"
    )

    for recipient_email in emails:
        if not recipient_email.strip():
            continue

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"Follow-up email sent to {recipient_email} at {datetime.datetime.now()}")
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(send_followup_emails, 'cron', hour=9, minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    os.makedirs("temp_uploads", exist_ok=True)
    app.run(debug=True, port=5000)
