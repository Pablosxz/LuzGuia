import json, os, boto3
from twilio.rest import Client

from Utils.invokeBackend import invokeBackend
from Utils.polly import pollySpeech, sendAudioMessage

def sqsProcess_handler(event, context):
    
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    queue_url = os.environ['SQS_QUEUE_URL']
    
    twilio_client = Client(account_sid, auth_token)
    s3_client = boto3.client('s3')
    sqs_client = boto3.client('sqs')
    
    for record in event['Records']:
        try:
            # Desserializa a mensagem JSON
            message_body = json.loads(record['body'])
            
            # Extrai os dados da mensagem
            data = message_body['data']
            payload = message_body['payload']
            my_number = data['my_number']
            guest_number = data['guest_number']
            
            
            print(f"Processando mensagem para {guest_number}")
            
            # Invoca o backend para processar a imagem
            message_response = invokeBackend(data, payload)
            
            if 'Payload' in message_response:
                payload_content = message_response['Payload']
                
                try:
                    # Converta o StreamingBody para string
                    payload_content_str = payload_content.read().decode('utf-8')
                    payload_content_json = json.loads(payload_content_str)

                    print(f"Mensagem processada. Resposta do backend: {payload_content_json}")
                    
                    payload_content_body = payload_content_json['body']
                    
                    # Envie a resposta via WhatsApp usando Twilio
                    twilio_msg = twilio_client.messages.create(
                        body=payload_content_body,
                        from_=my_number,
                        to=guest_number
                    )
                    
                    # Manda o áudio
                    sendAudioMessage(payload_content_body, guest_number, s3_client, twilio_client, my_number)
                    
                    print(f"Mensagem enviada para {guest_number}: {twilio_msg.sid}")
                    response = {
                        "statusCode": 200,
                        "body": "Mensagem processada com sucesso"
                    }
                
                except Exception as e:
                    print(f"Erro ao processar o payload: {str(e)}")
                
            else:
                print("Payload não encontrado na resposta do backend.")
                response = {
                        "statusCode": 400,
                        "body": "Erro ao enviar mensagem do SQS"
                    }
            
            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=record['receiptHandle']
            )
            print("Mensagem apagada da fila SQS.")
            return response
        
            
        except Exception as e:
            print(f"Erro ao processar a mensagem: {e}")
            return {
                "statusCode": 500,
                "body": "Erro ao processar a mensagem"
            }
