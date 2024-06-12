import json
import boto3
from Utils.bularioAPI import bularioHandler
from Utils.bedrock import answerQuestion, formatText
from Utils.textract import extractTextFromImage

from twilio.rest import Client
import os

def backend_handler(event, context):
    
    print("Iniciando Lambda de Lex Handler")
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    
    twilio_client = Client(account_sid, auth_token)
    
    
    payload = event.get('payload')
    data = event.get('data')
    
    print("Payload: ", payload)
    print("Data: ", data)
    
    funcionality = data.get('functionality')
    s3_key = payload.get('s3_key')
    guest_number = data.get('guest_number')
    my_number = data.get('my_number')
    
    print(f"Funcionality: {funcionality}")
    print(f"S3 Key: {s3_key}")
    print(f"Guest Number: {guest_number}")
    
    if funcionality == 'remedio':
        try:
            # Pega o texto da bula
            text, pdf_key = bularioHandler(s3_key)
            
            if text:
                
                # Resume o texto da bula
                resume = answerQuestion(text, "Quais são as principais informações que eu deveria saber sobre este remédio?")
                resume = formatText(resume)
                
                response = {
                    "statusCode": 200, 
                    "body": resume
                }
                s3_client = boto3.client('s3')
                # Manda o arquivo PDF
                presigned_url = s3_client.generate_presigned_url('get_object',
                    Params={'Bucket': os.environ['S3_BUCKET_NAME'], 'Key': pdf_key},
                    ExpiresIn=360)  # URL válida por 6 minutos
                print("pdf_key: ",pdf_key)
                print("presigned_url", presigned_url)

                message = twilio_client.messages.create(
                media_url=[presigned_url], # URL do PDF
                from_=my_number,
                to=guest_number
                )
                
                return response
            
            return {
                "statusCode": 200,
                "body": "Erro ao buscar a bula do remédio"
                }
        except Exception as e:
            print(f"Erro ao buscar bula: {e}")
            
            return {
                "statusCode": 200,
                "body": "Erro ao buscar a bula do remédio"
            }
    elif funcionality == 'documento':
        try:
            
            response = extractTextFromImage(s3_key)
            
            response = {
                "statusCode": 200,
                "body": "Retorno: " + response
            }
            
            return response
        except Exception as e:
            print(f"Erro ao buscar informações no ambiente: {e}")
            return None
