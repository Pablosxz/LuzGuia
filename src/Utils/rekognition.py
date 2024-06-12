import json
import boto3
from dotenv import load_dotenv
import os

def reconhecerTexto(imageBytes):
    try:
        rekognition = boto3.client("rekognition")
        
        rekognitionResponse = rekognition.detect_text(
            Image={
                'Bytes': imageBytes
            },
            Filters={
                'WordFilter': {
                    'MinConfidence': 70
                }
            }
        )
        texts = [
            {
                'detectedText': text['DetectedText']
                # 'Confidence': label["Confidence"]
                }
                for text in rekognitionResponse['TextDetections'] if text['Type']=='LINE'
            ]
        response = {"statusCode": 200, "body": json.loads(json.dumps(texts))}

    except Exception as e:
        response = {"statusCode": 500, "body": f"Exceção: {str(e)}"}
    
    return response


# Reconhecimento de objetos
def detect_labels_s3(bucket, photo):

    rekognition = boto3.client("rekognition")
    
    try:
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': photo,
                }
            },
            MaxLabels=10  # Número máximo de labels a serem retornadas
        )
        return response['Labels']
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []


def lambda_handler(event, context):
    load_dotenv()
    bucket = os.getenv("S3_BUCKET_NAME")
    photo = 'download.jpg'
    labels = detect_labels_s3(bucket, photo)
    for label in labels:
        print(f"Label: {label['Name']}, Confidence: {label['Confidence']:.2f}%")