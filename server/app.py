import os
import re
from flask import Flask, request, jsonify, send_from_directory, url_for, redirect
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import boto3
from botocore.exceptions import ClientError
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
load_dotenv()

# MySQL Database Configuration
DB_CONFIG = {
    'host': os.environ.get('RDS_HOST'),
    'user': os.environ.get('RDS_USER'),
    'password': os.environ.get('RDS_PASSWORD'),
    'database': os.environ.get('RDS_DATABASE')
}

# S3 Configuration
S3_BUCKET = os.environ.get('S3_BUCKET')  # Replace with your bucket name
S3_UPLOAD_FOLDER = 'uploads/'
S3_OUTPUT_FOLDER = 'output/'
S3_USER_FOLDER = 'user/'

# Local folders (fallbacks used when running locally)
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', os.path.join(os.getcwd(), 'output'))

# Ensure local folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# AWS S3 client setup
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),      # Replace with your access key
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),  # Replace with your secret key
    region_name='ap-south-1'                 # Replace with your region (e.g., 'us-east-1')
)

def upload_file_to_s3(file_obj, folder, filename):
    """Upload a file to S3 bucket in specified folder"""
    try:
        key = f"{folder}{filename}"
        s3_client.upload_fileobj(file_obj, S3_BUCKET, key)
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"
        return url
    except ClientError as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

def delete_file_from_s3(folder, filename):
    """Delete a file from S3 bucket"""
    try:
        key = f"{folder}{filename}"
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError as e:
        print(f"Error deleting from S3: {str(e)}")
        return False

def get_s3_presigned_url(folder, filename, expiration=3600):
    """Generate a presigned URL for an S3 object"""
    try:
        key = f"{folder}{filename}"
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {str(e)}")
        return None

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
    """Return a mysql.connector connection or None."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG.get('host'),
            user=DB_CONFIG.get('user'),
            password=DB_CONFIG.get('password'),
            database=DB_CONFIG.get('database'),
            autocommit=False
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

# Initialize Database Tables
def init_db():
    conn = get_db_connection()
    if not conn:
        print("Can't initialize DB - no connection")
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone CHAR(10) NOT NULL, 
                password VARCHAR(255) NOT NULL,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                license_number VARCHAR(255),
                dob VARCHAR(255),
                years_of_experience INT,
                clinic_address TEXT,
                profile_image TEXT,
                specialization VARCHAR(255)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                doctor_id INT NOT NULL,
                first_name VARCHAR(255) NOT NULL,
                last_name VARCHAR(255) NOT NULL,
                age INT NOT NULL,
                gender VARCHAR(50) NOT NULL,
                clinical_history TEXT NOT NULL,
                medical_image TEXT,
                organ VARCHAR(255) NOT NULL,
                disease VARCHAR(255) NOT NULL,
                features TEXT,
                disease_image TEXT,
                report TEXT NOT NULL,
                report_pdf LONGBLOB,
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                doctor_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(255) NOT NULL,
                likes INT DEFAULT 0,
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT NOT NULL,
                doctor_id INT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        conn.commit()
    except Error as e:
        print(f"Error initializing DB: {e}")
    finally:
        cursor.close()
        conn.close()

# Initialize the database
init_db()


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
    
    # Save as JPG into the provided output_folder (use the temp dir when provided)
    output_filename = os.path.join(output_folder, os.path.splitext(os.path.basename(dicom_path))[0] + ".jpg")
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

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM doctors WHERE email = %s', (email,))
        doctor = cursor.fetchone()
        if doctor and check_password_hash(doctor['password'], password):
            return jsonify({"message": "Login successful", "id": doctor['id']}), 200
        return jsonify({"message": "Invalid email or password"}), 401
    finally:
        cursor.close()
        conn.close()

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
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection error"}), 500
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('INSERT INTO doctors (first_name, last_name, email, phone, password) VALUES (%s,%s,%s,%s,%s)', 
                         (fname, lname, email, phone, hashed_password))
            conn.commit()
            cursor.execute('SELECT * FROM doctors WHERE email = %s', (email,))
            doctor = cursor.fetchone()
            return jsonify({"message": "Signup successful!","id": doctor['id']}), 201
        finally:
            cursor.close()
            conn.close()
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Email already exists"}), 400

@app.route('/dashboard/<int:doctor_id>', methods=['GET'])
def get_dashboard(doctor_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    
    cursor = None  # Initialize cursor to None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Fetch doctor details
        cursor.execute('SELECT first_name, last_name FROM doctors WHERE id = %s', (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            return jsonify({"message": "Doctor not found"}), 404

        # Fetch total number of patients
        cursor.execute('SELECT COUNT(*) as count FROM reports WHERE doctor_id = %s', (doctor_id,))
        total_patients = cursor.fetchone()['count']

        # Fetch critical patients
        cursor.execute(
            "SELECT id, first_name, last_name, features FROM reports WHERE doctor_id = %s", 
            (doctor_id,)
        )
        critical_patients = cursor.fetchall()

        # Process the results for critical patients
        critical_patients_list = []
        for patient in critical_patients:
            # Safely parse JSON features
            try:
                features = json.loads(patient["features"]) if patient["features"] else []
            except json.JSONDecodeError:
                features = [] # Handle cases where features are not valid JSON

            # Check if any feature has severity = "severe"
            if any(isinstance(feature, list) and len(feature) > 5 and feature[5] == "severe" for feature in features):
                critical_patients_list.append({
                    "id": patient["id"],
                    "name": f"{patient['first_name']} {patient['last_name']}"
                })

        return jsonify({
            "doctor_name": f"{doctor['first_name']} {doctor['last_name']}",
            "total_patients": total_patients,
            "critical_patients": critical_patients_list
        }), 200

    except Error as e:
        # Log the specific database error for debugging
        print(f"Database error: {e}")
        return jsonify({"message": "An error occurred while fetching dashboard data."}), 500
    except Exception as e:
        # Log any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return jsonify({"message": "An internal server error occurred."}), 500
        
    finally:
        # Ensure the cursor and connection are always closed
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    
# Fetch Doctor Profile
@app.route('/doctor/<int:doctor_id>', methods=['GET'])
def get_doctor_profile(doctor_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM doctors WHERE id = %s', (doctor_id,))
        doctor = cursor.fetchone()
        if not doctor:
            return jsonify({"message": "Doctor not found"}), 404
        return jsonify(doctor), 200
    finally:
        cursor.close()
        conn.close()


# Update Doctor Profile
@app.route('/doctor/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.form
    profile_image = request.files.get('profile_image')
    print("image received")
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM doctors WHERE id = %s', (doctor_id,))
        doctor = cursor.fetchone()
        if not doctor:
            return jsonify({"message": "Doctor not found"}), 404

        # Handle profile image upload
        image_url = doctor['profile_image']
        if profile_image:
            filename = secure_filename(f"doctor_{doctor_id}_profile.jpg")
            image_url = upload_file_to_s3(profile_image, S3_USER_FOLDER, filename)
            if not image_url:
                return jsonify({"message": "Failed to upload image"}), 500

        cursor.execute('''
            UPDATE doctors
            SET first_name = %s, last_name = %s, license_number = %s, dob=%s,
                years_of_experience = %s, clinic_address = %s, email = %s, specialization = %s, profile_image = %s
            WHERE id = %s
        ''', (
            data['firstName'], data['lastName'], data['licenseNumber'], data['dob'],
            data['yearsOfExperience'], data['clinicAddress'], data['email'], data['specialization'],
            image_url, doctor_id
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

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

    # Create a temporary directory for processing
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    image_path = None
    
    try:
        if medical_image.filename.lower().endswith(".dcm"):
            filename = secure_filename(f"{first_name}_{last_name}_{medical_image.filename}")
            temp_path = os.path.join(temp_dir, filename)
            medical_image.save(temp_path)
            
            # Convert DICOM to JPG
            jpg_path = dicom_to_jpg(temp_path, temp_dir, dicom_value)
            filename = secure_filename(f"{first_name}_{last_name}_{medical_image.filename[0]}.jpg")
            image_path = jpg_path
            
            # Upload JPG to S3
            with open(jpg_path, 'rb') as jpg_file:
                image_url = upload_file_to_s3(jpg_file, S3_UPLOAD_FOLDER, filename)
                if not image_url:
                    return jsonify({"message": "Failed to upload image"}), 500

        if medical_image and not medical_image.filename.lower().endswith(".dcm"):
            filename = secure_filename(f"{first_name}_{last_name}_{medical_image.filename}")
            # Save temporarily for processing
            temp_path = os.path.join(temp_dir, filename)
            medical_image.save(temp_path)
            image_path = temp_path
            
            # Upload to S3
            medical_image.seek(0)
            image_url = upload_file_to_s3(medical_image, S3_UPLOAD_FOLDER, filename)
            if not image_url:
                return jsonify({"message": "Failed to upload image"}), 500
    except Exception as e:
    # It's a good practice to log the actual error for debugging
        print(f"An error occurred: {e}") 
        return jsonify({"message": "An internal server error occurred during file processing."}), 500

    try:
        # Use S3-based prediction flow: call predict.predict_from_s3 which downloads the upload,
        # runs local inference, uploads the output image to S3, and returns the result.
        print("Calling predict.predict_from_s3 on S3 upload key...")
        upload_key = f"{S3_UPLOAD_FOLDER}{filename}"
        predict_result = predict.predict_from_s3(upload_key, filename, S3_BUCKET, s3_client=s3_client, uploads_prefix=S3_UPLOAD_FOLDER, output_prefix=S3_OUTPUT_FOLDER)
        print("Predict result:", predict_result)

        if predict_result.get('error'):
            return jsonify({"message": "Prediction failed", "detail": predict_result.get('error')}), 500

        disease = predict_result.get('disease')
        features = predict_result.get('features', [])
        organ = predict_result.get('organ') or None
        output_key = predict_result.get('output_key')

        # Handle DICOM special-case mapping (keep previous behavior)
        if organ == "brain-dcm":
            organ = "Brain"
            dcm = True

        # If DICOM and we want to force healthy (previous behavior), override
        if dcm:
            disease = "healthy"
            features = []

        # Prepare the report
        if organ == "Liver-Tumor" or organ == "Liver-Disease" or organ == "Brain":
            if organ != "Brain":
                organ = "Liver"
            response = report2.report(embedding_model, organ, age, clinical_history, disease, features)
        else:
            if isinstance(disease, list) or disease == "stone":
                # kidney stone or list-handling
                if disease == "stone":
                    response = report2.report(embedding_model, organ, age, clinical_history, disease, features)
                else:
                    response = report2.report(embedding_model, organ, age, clinical_history, disease)
            else:
                response = report2.report(embedding_model, organ, age, clinical_history, disease)

        # Build the external URL that redirects to a presigned S3 URL (if output was produced)
        output_url = None
        if output_key:
            output_filename = os.path.basename(output_key)
            output_url = url_for('serve_output_file', filename=output_filename, _external=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor()
        if organ=="Liver" or organ=="Brain" or disease=="stone":
            features = json.dumps(features)
            if isinstance(disease, list):
                disease = json.dumps(disease)
            cursor.execute(
                '''INSERT INTO reports (doctor_id, first_name, last_name, age, gender, clinical_history, medical_image, organ, disease, features, disease_image, report)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (doctor_id, first_name, last_name, age, gender, clinical_history, image_url, organ, disease, features, output_url, response)
            )
            conn.commit()
        else:
            cursor.execute(
                '''INSERT INTO reports (doctor_id, first_name, last_name, age, gender, clinical_history, medical_image, organ, disease, disease_image, report)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (doctor_id, first_name, last_name, age, gender, clinical_history, image_url, organ, disease, output_url, response)
            )
            conn.commit()

        report_id = cursor.lastrowid
        # print(report_id)
        return jsonify({"message": "Report created successfully", "report_id": report_id}), 201
    finally:
        cursor.close()
        conn.close()


# Fetch Reports for a Doctor
@app.route('/reports/<int:doctor_id>', methods=['GET'])
def get_reports(doctor_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, first_name, last_name, age, clinical_history, disease, features FROM reports WHERE doctor_id = %s', (doctor_id,))
        reports = cursor.fetchall()

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
    finally:
        cursor.close()
        conn.close()


# Fetch a Single Report by ID
@app.route('/view-report/<int:report_id>', methods=['GET'])
def get_report(report_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM reports WHERE id = %s', (report_id,))
        report = cursor.fetchone()
        if not report:
            return jsonify({"message": "Report not found"}), 404
        cursor.execute('SELECT * FROM doctors WHERE id = %s', (report["doctor_id"],))
        doctor = cursor.fetchone()
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
    finally:
        cursor.close()
        conn.close()


@app.route("/upload-report", methods=["POST"])
def upload_report():
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
    # Read the PDF data (we keep this for storing in DB) and upload to S3
    pdf_data = file.read()
    file.seek(0)
    try:
        s3_uploaded = upload_file_to_s3(file, S3_UPLOAD_FOLDER, filename)
        if not s3_uploaded:
            return jsonify({"message": "Failed to upload PDF to S3"}), 500
    except Exception as e:
        print(f"Error uploading PDF to S3: {e}")
        return jsonify({"error": "Failed to upload PDF to S3"}), 500

    # Save the binary PDF data in the database
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE reports SET report_pdf = %s WHERE id = %s", (pdf_data, record_id))
        conn.commit()
        return jsonify({"message": "Report uploaded successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cursor.close()
        except:
            pass
        conn.close()

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
            conn = get_db_connection()
            if not conn:
                return jsonify({"message": "Database connection error"}), 500
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT report_pdf FROM reports WHERE id = %s", (record_id,))
                pdf_data = cursor.fetchone()
            finally:
                cursor.close()
                conn.close()
            
            print("Fetched pdf_data:", pdf_data)  # Debugging

            if pdf_data and pdf_data.get("report_pdf"):
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
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM posts')
        posts = cursor.fetchall()
        posts_data = []
        for post in posts:
            cursor.execute('SELECT * FROM comments WHERE post_id = %s', (post['id'],))
            comments = cursor.fetchall()
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
    finally:
        cursor.close()
        conn.close()

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

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (doctor_id, title, content, category) VALUES (%s, %s, %s, %s)',
                     (doctor_id, title, content, category))
        conn.commit()
        return jsonify({"message": "Post created successfully"}), 201
    finally:
        cursor.close()
        conn.close()

# Forum: Add a Comment to a Post
@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    content = data.get("content")

    if not all([doctor_id, content]):
        return jsonify({"message": "All fields are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (post_id, doctor_id, content) VALUES (%s, %s, %s)',
                     (post_id, doctor_id, content))
        conn.commit()
        return jsonify({"message": "Comment added successfully"}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    url = get_s3_presigned_url(S3_UPLOAD_FOLDER, filename)
    if url:
        return redirect(url)
    return jsonify({"message": "File not found"}), 404

# Serve output images
@app.route('/output/<filename>')
def serve_output_file(filename):
    url = get_s3_presigned_url(S3_OUTPUT_FOLDER, filename)
    if url:
        return redirect(url)
    return jsonify({"message": "File not found"}), 404

@app.route('/user/<filename>')
def serve_user_image(filename):
    url = get_s3_presigned_url(S3_USER_FOLDER, filename)
    if url:
        return redirect(url)
    return jsonify({"message": "File not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
