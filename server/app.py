import os
import re
from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import predict, report2
import smtplib
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from flask_mail import Mail, Message
import pydicom
import numpy as np
import cv2

# Flask App Setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# SQLite Database
DATABASE = 'doctors.db'
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
USER_FOLDER='user'


# Configure app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['USER_FOLDER'] = USER_FOLDER
if not os.path.exists(USER_FOLDER):
    os.makedirs(USER_FOLDER)

app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Use your email provider's SMTP
app.config["MAIL_PORT"] = 587  # 465 for SSL, 587 for TLS
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = "team.datagurus@gmail.com"  # Your email
app.config["MAIL_PASSWORD"] = "mkdef ctbu wgcx lkhd"  # Use App Password if using Gmail
app.config["MAIL_DEFAULT_SENDER"] = "team.datagurus@gmail.com"
mail=Mail(app)


def generate_otp(length=6):
    """Generate a random numeric OTP of given length."""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(recipient_email, otp):
    """Send a stylish HTML email with the OTP and company branding."""

    sender_email = "team.datagurus@gmail.com"  # Replace with your email
    sender_password = "kdef ctbu wgcx lkhd"  # Use an App Password

    subject = str(Header("🔐 Secure OTP Verification - Your Company", "utf-8"))

    logo_path = "/Sanjeevani_AI_logo.jpg"  # Ensure correct path

    # HTML Email Body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                text-align: center;
            }}
            .container {{
                background: white;
                width: 80%;
                margin: auto;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }}
            .otp {{
                font-size: 24px;
                font-weight: bold;
                color: #e74c3c;
            }}
            .footer {{
                font-size: 12px;
                color: #777;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="cid:company_logo" width="200" alt="Company Logo">
            <h2>🔒 Your One-Time Password (OTP)</h2>
            <p>Dear User,</p>
            <p>Use the OTP below to complete your authentication:</p>
            <p class="otp">{otp}</p>
            <p>This OTP is valid for 10 minutes. Do not share it with anyone.</p>
            <p class="footer">© 2025 Sanjeevani AI. All rights reserved.</p>
        </div>
    </body>
    </html>
    """

    # Create email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    # Attach logo image (only once)
    try:
        with open(logo_path, 'rb') as img:
            logo = MIMEImage(img.read(), name="Sanjeevani_AI_logo.jpg")
            logo.add_header('Content-ID', '<company_logo>')
            msg.attach(logo)
    except FileNotFoundError:
        print("⚠️ Logo image not found. Email sent without logo.")

    try:
        # Set up the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email (proper UTF-8 handling)
        server.sendmail(sender_email, recipient_email, msg.as_string().encode('utf-8'))
        server.quit()

        print("✅ Stylish OTP email sent successfully!")
    except Exception as e:
        print(f"❌ General error: {e}")
# Database Connection Helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize Database Tables
with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            phone CHAR(10) NOT NULL, 
            password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            license_number TEXT,
            dob TEXT,
            years_of_experience INTEGER,
            clinic_address TEXT,
            profile_image TEXT,
            specialization TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            clinical_history TEXT NOT NULL,
            medical_image TEXT,
            organ TEXT NOT NULL,
            disease TEXT NOT NULL,
            features TEXT,
            disease_image TEXT,
            report TEXT NOT NULL,
            report_pdf BLOB,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')
    conn.commit()


otpdb={}

def select_best_frame(dicom_image, method):
    """
    Selects the most appropriate frame based on the chosen method.
    Methods:
    - "middle": Selects the middle frame.
    - "max_intensity": Selects the frame with the highest pixel intensity sum.
    - "largest_roi": Selects the frame with the largest non-zero pixel area.
    - "edges": Selects the frame with the most detected edges.
    """
    if len(dicom_image.pixel_array.shape) == 3:  # Multi-frame DICOM
        frames = dicom_image.pixel_array
        num_frames = frames.shape[0]

        if method == "middle":
            best_frame = frames[num_frames // 2]  # Middle frame
        
        elif method == "max_intensity":
            intensity_sums = [np.sum(frame) for frame in frames]
            best_frame = frames[np.argmax(intensity_sums)]  # Frame with highest intensity
        
        elif method == "largest_roi":
            non_zero_counts = [np.count_nonzero(frame) for frame in frames]
            best_frame = frames[np.argmax(non_zero_counts)]  # Frame with the largest non-zero area
        
        elif method == "edges":
            edge_counts = []
            for frame in frames:
                edges = cv2.Canny(frame.astype(np.uint8), 50, 150)
                edge_counts.append(np.sum(edges))  # Count the number of edges
            best_frame = frames[np.argmax(edge_counts)]  # Frame with most edges
        
        else:
            raise ValueError("Invalid method. Choose from 'middle', 'max_intensity', 'largest_roi', or 'edges'.")
        
        return best_frame
    else:
        return dicom_image.pixel_array  # Single-frame DICOM

def dicom_to_jpg(dicom_path, output_folder, method):
    """
    Converts the best-selected DICOM frame to JPG.
    """
    dicom_image = pydicom.dcmread(dicom_path)
    
    # Select the best frame based on user choice
    best_frame = select_best_frame(dicom_image, method)

    # Normalize pixel values
    best_frame = (best_frame - np.min(best_frame)) / (np.max(best_frame) - np.min(best_frame)) * 255.0
    best_frame = best_frame.astype(np.uint8)
    
    # Convert to RGB if grayscale
    if len(best_frame.shape) == 2:
        best_frame = cv2.cvtColor(best_frame, cv2.COLOR_GRAY2RGB)
    
    # Save as JPG
    output_filename=os.path.join(app.config['UPLOAD_FOLDER'], os.path.splitext(os.path.basename(dicom_path))[0] + ".jpg")
    # output_filename = os.path.join(output_folder, )
    cv2.imwrite(output_filename, best_frame)
    
    return output_filename


os.environ["PINECONE_API_KEY"] = "pcsk_76sA86_9DeHgRYds1BXvcndMbEyvKKtUrqPTeuUfbnVsdTm3PHQGi1yjix16aEvWRpHuQj"
print("Loading embedding model...")
embedding_model = HuggingFaceEmbeddings(model_name="abhinand/MedEmbed-large-v0.1")
print(embedding_model)
    # os.environ["PINECONE_API_KEY"] = "pcsk_kPX7Z_7uouP3ZtasKTnxdxmv1Xq78CbDFgHi7X1d5NKbAAYs2MjanRU87uLujvaVAFTde"
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    print(email)

    if not email:
        return jsonify({"message": "Email is required"}), 400

    otp = generate_otp()
    otpdb[email] = otp
    print(otp)

    try:
        send_otp_email(email, otp)
        response = jsonify({"message": "OTP sent successfully!"})
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response, 200
    except Exception as e:
        return jsonify({"message": f"Failed to send OTP: {str(e)}"}), 500
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if otpdb.get(email) == otp:
        del otpdb[email]  # Remove OTP after successful verification
        return jsonify({"message": "OTP verified successfully!"}), 200
    else:
        return jsonify({"message": "Invalid or expired OTP"}), 400
    

# Sign-in Endpoint
@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    with get_db_connection() as conn:
        doctor = conn.execute('SELECT * FROM doctors WHERE email = ?', (email,)).fetchone()
        if doctor and check_password_hash(doctor['password'], password):
            return jsonify({"message": "Login successful", "id": doctor['id']}), 200
    return jsonify({"message": "Invalid email or password"}), 401

# Sign-up Endpoint
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    fname=data.get('firstName')
    lname=data.get('lastName')
    phone=data.get('phone')
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    try:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        with get_db_connection() as conn:
            conn.execute('INSERT INTO doctors (first_name, last_name, email, phone, password) VALUES (?,?,?,?,?)', (fname, lname, email, phone, hashed_password))
            conn.commit()
        doctor = conn.execute('SELECT * FROM doctors WHERE email = ?', (email,)).fetchone()
        return jsonify({"message": "Signup successful!","id": doctor['id']}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Email already exists"}), 400

@app.route('/dashboard/<int:doctor_id>', methods=['GET'])
def get_dashboard(doctor_id):
    with get_db_connection() as conn:
        # Fetch doctor details
        doctor = conn.execute('SELECT first_name, last_name FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
        
        if not doctor:
            return jsonify({"message": "Doctor not found"}), 404

        # Fetch total number of patients
        total_patients = conn.execute('SELECT COUNT(*) FROM reports WHERE doctor_id = ?', (doctor_id,)).fetchone()[0]

        # Fetch critical patients
        critical_patients = conn.execute(
            "SELECT id, first_name, last_name, features FROM reports WHERE doctor_id = ?", 
            (doctor_id,)
            ).fetchall()

# Process the results
        critical_patients_list = []

        for patient in critical_patients:
            features = json.loads(patient["features"]) if patient["features"] else []  # Convert from string to list

    # Check if any feature has severity = "severe"
            if any(feature[5] == "severe" for feature in features):
                    critical_patients_list.append({
                    "id": patient["id"],
                    "name": f"{patient['first_name']} {patient['last_name']}"
                })

        return jsonify({
            "doctor_name": f"{doctor['first_name']} {doctor['last_name']}",
            "total_patients": total_patients,
            "critical_patients": critical_patients_list
        }), 200

    
# Fetch Doctor Profile
@app.route('/doctor/<int:doctor_id>', methods=['GET'])
def get_doctor_profile(doctor_id):
    with get_db_connection() as conn:
        doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
        if not doctor:
            return jsonify({"message": "Doctor not found"}), 404

        doctor_data = dict(doctor)
        return jsonify(doctor_data), 200


# Update Doctor Profile
@app.route('/doctor/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.form
    profile_image = request.files.get('profile_image')
    print("image received")
    with get_db_connection() as conn:
        doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
        if not doctor:
            return jsonify({"message": "Doctor not found"}), 404

        # Handle profile image upload
        image_url = doctor['profile_image']
        if profile_image:
            filename = secure_filename(f"doctor_{doctor_id}_profile.jpg")
            image_path = os.path.join(app.config['USER_FOLDER'], filename)
            profile_image.save(image_path)
            image_url = url_for('serve_user_image', filename=filename, _external=True)

        conn.execute('''
            UPDATE doctors
            SET first_name = ?, last_name = ?, license_number = ?, dob=?,
                years_of_experience = ?, clinic_address = ?, email = ?, specialization = ?, profile_image = ?
            WHERE id = ?
        ''', (
            data['firstName'], data['lastName'], data['licenseNumber'], data['dob'],
            data['yearsOfExperience'], data['clinicAddress'], data['email'], data['specialization'],
            image_url, doctor_id
        ))
        conn.commit()
    
    return jsonify({"message": "Profile updated successfully"}), 200


# Generate Report Endpoint
@app.route('/report', methods=['POST'])
def generate_report():
    print("Request received")  # Add this to confirm the request is hitting Flask

    # Try logging request data
    print("Request form data:", request.form)
    print("Request files:", request.files)
    doctor_id = request.form.get('doctor_id')
  
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    age = request.form.get('age')
    gender=request.form.get('gender')
    clinical_history = request.form.get('clinical_history')
    dicom_value=request.form.get('dcm_value')
    print(dicom_value)
    medical_image = request.files.get('medical_image')
    print("Data fetched")
    dcm=False
    if not all([doctor_id, first_name, last_name, age, clinical_history]):
        return jsonify({"message": "All fields are required"}), 400

    if medical_image.filename.lower().endswith(".dcm"):
        filename = secure_filename(f"{first_name}_{last_name}_{medical_image.filename}")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        medical_image.save(image_path)

        # dicom_folder = "dicom_images"
        os.makedirs("uploads", exist_ok=True)
        
        image_path = dicom_to_jpg(image_path, "uploads", dicom_value)
        filename = secure_filename(f"{first_name}_{last_name}_{medical_image.filename[0]}.jpg")
        print(f"Best-selected frame converted to JPG: {image_path}")
        image_url = url_for('serve_uploaded_file', filename=filename, _external=True)

    if medical_image and not medical_image.filename.lower().endswith(".dcm"):
        filename = secure_filename(f"{first_name}_{last_name}_{medical_image.filename}")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        medical_image.save(image_path)
        image_url = url_for('serve_uploaded_file', filename=filename, _external=True)
    try:
        # Use the uploaded image path for processing
        print("Identifying organ...")
        organ = predict.predict_organ(image_path)
        if organ=="brain-dcm":
            organ="Brain"
          
            dcm=True
        print("organ: ",organ)
        print("Predicting disease and extracting features...")
        if organ == "Liver-Tumor" or organ=="Liver-Disease" or organ=="Brain":
            # print(organ)
            disease, features = predict.predict_disease(organ, image_path, filename)
            if dcm==True:
                disease="healthy"
                features=[]
            print(disease, features)
            if organ != "Brain":
                organ="Liver"
            print("Preparing the report")
            # print(organ)
            # print(age)
            # print(clinical_history)
            print(disease)
            print(features)
            print("Initiating report preparation")
            response = report2.report(embedding_model, organ, age, clinical_history, disease, features)
        else:
            disease = predict.predict_disease(organ, image_path, filename)
            print(disease)
            if disease=="stone":
                disease, features=predict.kidney_stone_model(image_path, filename)
                print(disease)
                print(features)
                print("Initiating report preparation")
                response = report2.report(embedding_model, organ, age, clinical_history, disease, features)
            else:
                # Ensure output folder exists
                output_folder = 'output'
                os.makedirs(output_folder, exist_ok=True)  # Create the output folder if it doesn't exist

        # Define output path and save the file
                output_path = os.path.join(output_folder, filename)
                medical_image.save(output_path)  # Save the file to the 'output' folder

            if organ=="Chest":
                organ="Lungs"
            # print(organ)
            if disease !="stone":
                print("Initiating report preparation")
                response = report2.report(embedding_model, organ, age, clinical_history, disease)
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        output_url = url_for('serve_output_file', filename=filename, _external=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    with get_db_connection() as conn:
        if organ=="Liver" or organ=="Brain" or disease=="stone":
            features = json.dumps(features)
            if isinstance(disease, list):
                disease = json.dumps(disease)
            conn.execute('''
            INSERT INTO reports (doctor_id, first_name, last_name, age, gender, clinical_history, medical_image, organ, disease, features, disease_image, report)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?)
        ''', (doctor_id, first_name, last_name, age, gender, clinical_history, image_url, organ, disease, features, output_url, response))
            conn.commit()
        else:
            conn.execute('''
                INSERT INTO reports (doctor_id, first_name, last_name, age, gender, clinical_history, medical_image, organ, disease, disease_image, report)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?)
            ''', (doctor_id, first_name, last_name, age, gender, clinical_history, image_url, organ, disease, output_url, response))
            conn.commit()

    report_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    # print(report_id)
    return jsonify({"message": "Report created successfully", "report_id": report_id}), 201


# Fetch Reports for a Doctor
@app.route('/reports/<int:doctor_id>', methods=['GET'])
def get_reports(doctor_id):
    with get_db_connection() as conn:
        reports = conn.execute('SELECT id, first_name, last_name, age, clinical_history, disease, features FROM reports WHERE doctor_id = ?', (doctor_id,)).fetchall()
        def extract_area(area):
                if isinstance(area, (int, float)):  # If already numeric, return as is
                    return float(area)
                if isinstance(area, str):  # If string, extract numbers
                    match = re.search(r"([\d\.]+)", area)
                    return float(match.group(1)) if match else 0
                return 0  # Default fallback
        updated_reports = []
        for report in reports:
            report_dict = dict(report)
            
            # Convert features from text to a list
            features = json.loads(report_dict["features"]) if report_dict["features"] else []
            
            # Determine severity from the feature with the highest area
            if features:
                max_area_feature = max(features, key=lambda x: extract_area(x[1])) # x[0] is area
                report_dict["severity"] = max_area_feature[5]  # x[4] is severity
            else:
                report_dict["severity"] = "Moderate"

            updated_reports.append(report_dict)

        return jsonify(updated_reports), 200


# Fetch a Single Report by ID
@app.route('/view-report/<int:report_id>', methods=['GET'])
def get_report(report_id):
    with get_db_connection() as conn:
        report = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (report["doctor_id"],)).fetchone()
        if not report:
            return jsonify({"message": "Report not found"}), 404
        data_dict = json.loads(report["report"].strip("```json\n").strip("```"))
        print(data_dict)
        # Constructing the response JSON
        # Extract relevant data from parsed report
        treatment_recommendations = data_dict.get("Treatment Recommendations", [])
        possible_causes = data_dict.get("Possible Causes", [])
        blood_tests = data_dict.get("Blood Tests", [])
        prescriptions = data_dict.get("Prescriptions", [])

        features=report["features"]
        try:
            features = json.loads(features) if features else []  # Convert JSON string to Python list
        except json.JSONDecodeError:
            features = []  # If decoding fails, return an empty list
        
        if report["organ"]=="Liver" or report["organ"]=="Brain" or report["disease"]=="stone":
            if len(features)>1:
                features.pop()
            report_data = {
            "doctor_name": f'Dr. {doctor["first_name"]} {doctor["last_name"]}',
            "doctor_email": doctor["email"],
            "doctor_phone": doctor["phone"],
            "patient_name": report["first_name"]+" "+report["last_name"],
            "patient_age": report["age"],
            "patient_gender": report["gender"],
            "diagnosis_image": report["disease_image"],
            "features": features,
            "treatment_recommendations": treatment_recommendations,
            "possible_cause": possible_causes,
            "blood_tests": blood_tests,
            "prescriptions": prescriptions,
            "disease": report["disease"]
        }
        else:
            report_data = {
            "doctor_name": f'Dr. {doctor["first_name"]} {doctor["last_name"]}',
            "doctor_email": doctor["email"],
            "doctor_phone": doctor["phone"],
            "patient_name": report["first_name"]+" "+report["last_name"],
            "patient_age": report["age"],
            "patient_gender": report["gender"],
            "diagnosis_image": report["medical_image"],
            "features": features,
            "treatment_recommendations": treatment_recommendations,
            "possible_cause": possible_causes,
            "blood_tests": blood_tests,
            "prescriptions": prescriptions,
            "disease": report["disease"]
        }
        
        return jsonify(report_data), 200


@app.route("/upload-report", methods=["POST"])
def upload_report():
    try:
        # Check if the request contains a file and record ID
        if "report_pdf" not in request.files or "record_id" not in request.form:
            return jsonify({"error": "Missing file or record ID"}), 400

        file = request.files["report_pdf"]
        record_id = request.form["record_id"]
        print("Data fetched successfully.")

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Secure the file name and store in the uploads folder
        filename = secure_filename(f"Medical_Report_{record_id}.pdf")
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # ✅ FIX: Read the file before saving it
        pdf_data = file.read()  # Read binary data
        file.seek(0)  # Reset the file pointer so it can be saved properly
        file.save(file_path)  # Now save the file

        # Save the binary PDF data in the database
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE reports SET report_pdf = ? WHERE id = ?",
                (pdf_data, record_id),
            )
            conn.commit()

        return jsonify({"message": "Report uploaded successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/send-email", methods=["POST"])
def send_email():
    try:
        report_text = request.json.get("report_text")
        include_attachment = request.json.get("include_attachment", False)
        record_id = request.json.get("record_id")  # Get report ID from request
        print("Received record_id:", record_id)

        recipient = "reports.datagurus@gmail.com"
        subject = "New Report Submitted"
        body = f"Report: {report_text}\nInclude Attachment: {include_attachment}"
        
        msg = Message(subject, recipients=[recipient], body=body)

        if include_attachment and record_id:
            with get_db_connection() as conn:
                pdf_data = conn.execute("SELECT report_pdf FROM reports WHERE id = ?", (record_id,)).fetchone()
            
            print("Fetched pdf_data:", pdf_data)  # Debugging

            if pdf_data:
                pdf_blob = pdf_data["report_pdf"]  # Extract the BLOB data using column name
                print("Extracted PDF data length:", len(pdf_blob))  # Debugging

                msg.attach("Medical_Report.pdf", "application/pdf", pdf_blob)
            else:
                return jsonify({"error": "No PDF found for this report"}), 400
        
        mail.send(msg)
        return jsonify({"message": "Email sent successfully!"}), 200

    except Exception as e:
        import traceback
        print("Email sending error:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Forum: Fetch All Posts with Comments
@app.route('/posts', methods=['GET'])
def get_posts():
    with get_db_connection() as conn:
        posts = conn.execute('SELECT * FROM posts').fetchall()
        posts_data = []
        for post in posts:
            comments = conn.execute('SELECT * FROM comments WHERE post_id = ?', (post['id'],)).fetchall()
            posts_data.append({
                "id": post["id"],
                "doctor_id": post["doctor_id"],
                "title": post["title"],
                "content": post["content"],
                "category": post["category"],
                "likes": post["likes"],
                "comments": [dict(comment) for comment in comments]
            })
        return jsonify(posts_data), 200

# Forum: Add a New Post
@app.route('/posts', methods=['POST'])
def add_post():
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    title = data.get("title")
    content = data.get("content")
    category = data.get("category")

    if not all([doctor_id, title, content, category]):
        return jsonify({"message": "All fields are required"}), 400

    with get_db_connection() as conn:
        conn.execute('INSERT INTO posts (doctor_id, title, content, category) VALUES (?, ?, ?, ?)',
                     (doctor_id, title, content, category))
        conn.commit()
    return jsonify({"message": "Post created successfully"}), 201

# Forum: Add a Comment to a Post
@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    content = data.get("content")

    if not all([doctor_id, content]):
        return jsonify({"message": "All fields are required"}), 400

    with get_db_connection() as conn:
        conn.execute('INSERT INTO comments (post_id, doctor_id, content) VALUES (?, ?, ?)',
                     (post_id, doctor_id, content))
        conn.commit()
    return jsonify({"message": "Comment added successfully"}), 201

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Serve output images
@app.route('/output/<filename>')
def serve_output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/user/<filename>')
def serve_user_image(filename):
    return send_from_directory(app.config['USER_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
