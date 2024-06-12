import boto3
import os
import json
from dotenv import load_dotenv

def extracaoDocumento(document_name):

    # Inicia serviço da AWS
    textract = boto3.client('textract')
    s3 = boto3.client('s3')

    # Coleta objeto com documento
    response = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=document_name)
    image_bytes = response['Body'].read()
    
    # Extrai textos do documento
    response = textract.detect_document_text(Document={'Bytes': image_bytes})

    # Coleta informações do documento
    text = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            text.append(item["Text"])

    # Monta resposta
    textResponse = {"statusCode": 200, "body": json.loads(json.dumps(text))}

    # Retorna texto extraido
    return textResponse


# Extrai o texto de um doxumento
def extractTextFromPdf(fileName):
    textract = boto3.client('textract')
    bucketName = os.getenv("S3_BUCKET_NAME")
    
    # Inicia a extração do texto
    response = textract.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucketName,
                'Name': fileName
            }
        }
    )

    job_id = response['JobId']
    print(f"Started job with id: {job_id}")

    # Espera o textract terminar a extração de texto
    while True:
        response = textract.get_document_text_detection(JobId=job_id)
        status = response['JobStatus']
        if status in ['SUCCEEDED', 'FAILED']:
            break

    if status == 'SUCCEEDED':
        extracted_text = ''
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                extracted_text += block['Text'] + '\n'
        return extracted_text
    else:
        raise Exception("Document text detection failed")


# Faz upload de um texto para o S3
def uploadTextToS3(text, fileName):
    load_dotenv()
    bucketName = os.getenv("S3_BUCKET_NAME")
    s3 = boto3.client('s3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token = os.getenv('AWS_SESSION_TOKEN')
                )
    response = s3.put_object(Body = text, Bucket = bucketName, Key = f"Bulastxt/{fileName}", ContentType='text/plain')
    return response


def extractTextFromImage(fileName):
    try:
        load_dotenv()
        textract = boto3.client('textract')
        bucketName = os.getenv("S3_BUCKET_NAME")
        
        if not bucketName:
            raise ValueError("S3_BUCKET_NAME is not set in the environment variables")

        print(f"Processing file: {fileName} in bucket: {bucketName}")
        # Chama o Textract para detectar o texto no documento
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucketName,
                    'Name': fileName
                }
            }
        )
        if 'Blocks' not in response:
            raise ValueError("No text detected in the document")

        extracted_text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                extracted_text += item['Text'] + "\n"
        return extracted_text
    except Exception as e:
        print("Erro ao extrair texto do documento: ", e)
        return None