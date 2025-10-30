import os
import json
import boto3
import predict  # This imports your existing predict.py file

# Initialize the S3 client outside the handler for reuse
s3_client = boto3.client('s3')

def handler(event, context):
    
    # 1. Parse the incoming event
    # We expect the Flask app to send us the bucket and image key (path)
    try:
        body = json.loads(event['body'])
        bucket_name = body['bucket']
        s3_key = body['key'] # e.g., "uploads/patient_image.jpg"
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Error parsing input event: {str(e)}")
        }

    # Define local file paths within Lambda's temporary storage
    # This is the only writable directory in Lambda
    local_image_path = f"/tmp/{os.path.basename(s3_key)}"
    local_output_filename = f"output_{os.path.basename(s3_key)}"
    local_output_path = f"/tmp/{local_output_filename}"

    try:
        # 2. Download the image from S3 to the Lambda's /tmp folder
        s3_client.download_file(bucket_name, s3_key, local_image_path)
        
        # 3. --- Run your ML models ---
        print("Running predict_organ...")
        organ = predict.predict_organ(local_image_path)
        
        if organ == "brain-dcm":
            organ = "Brain"
        if organ == "Chest":
            organ = "Lungs"
        
        print(f"Organ: {organ}. Running predict_disease...")
        
        # We pass the local_output_path to tell predict.py where to save the output image
        disease, features = predict.predict_disease(
            organ, 
            local_image_path, 
            local_output_path  # This is the path to save the output image
        )
        
        print(f"Disease: {disease}. Uploading output image...")

        # 4. Upload the processed (output) image back to S3
        output_s3_key = f"output/{local_output_filename}"
        s3_client.upload_file(local_output_path, bucket_name, output_s3_key)
        
        # 5. Return a successful response to the Flask app
        return {
            'statusCode': 200,
            'body': json.dumps({
                'organ': organ,
                'disease': disease,
                'features': features,
                'output_image_s3_key': output_s3_key
            })
        }

    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Internal server error: {str(e)}")
        }