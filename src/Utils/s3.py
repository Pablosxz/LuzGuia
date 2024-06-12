import boto3
import os
from dotenv import load_dotenv


# Verifica se existe um objeto com esse nome no S3
def checkObjectExists(fileName):
    load_dotenv()
    bucketName = os.getenv("S3_BUCKET_NAME")
    s3 = boto3.client("s3",
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token = os.getenv('AWS_SESSION_TOKEN')
                )
    try:
        s3.head_object(Bucket=bucketName, Key=fileName)
        return True
    except s3.exceptions.NoSuchKey:
        return False
    except Exception as e:
        print(f"Erro ao verificar o objeto no S3: {e}")
        return False


# Faz download de um arquivo do S3
def getPdfFromS3(fileName, isNotPDF=0):
    load_dotenv()
    bucketName = os.getenv("S3_BUCKET_NAME")
    s3 = boto3.client('s3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token = os.getenv('AWS_SESSION_TOKEN')
                )
    response = s3.get_object(
        Bucket = bucketName,
        Key = fileName
    )
    if isNotPDF:
        pdfContent= response['Body'].read().decode('utf-8')
    else:
        pdfContent= response['Body'].read()
    return pdfContent