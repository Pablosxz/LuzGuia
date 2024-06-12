import json
import boto3
import os
import base64
import requests

from twilio.rest import Client
from botocore.exceptions import BotoCoreError, ClientError
from Utils.polly import pollySpeech, sendAudioMessage
from Utils.decodeResponse import decode_text_to_dict
from Utils.imagePrincipal import imagePrincipal
from Utils.lastResponse import get_last_message_sent_to_user
from Utils.sendMessageSQS import send_message_to_sqs

def preProcess_handler(event, context):
    try:
        # Inicializa clientes Boto3
        lex_client = boto3.client('lexv2-runtime')
        s3_client = boto3.client('s3')

        # Configurações do Twilio
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        
        twilio_client = Client(account_sid, auth_token)
        
        # Extrai as informações do corpo da mensagem
        body = decode_text_to_dict(base64.b64decode(event['body']))
            
        # Log no CloudWatch
        print(body)
        
        # Informações da mensagem
        message_body = body['Body']
        my_number = body['To']
        num_media = body['NumMedia']
        guest_number = body['From']
        message_type = body['MessageType']
        
        # Tenta pegar a URL da mídia e o tipo de conteúdo da mídia
        media_url = body.get('MediaUrl0')
        media_content_type = body.get('MediaContentType0')
        
        # Dicionário com os dados da mensagem
        data = {
            'account_sid': account_sid,
            'auth_token': auth_token,
            'message_body': message_body,
            'my_number': my_number,
            'num_media': num_media,
            'guest_number': guest_number,
            'message_type': message_type,
            'media_url': media_url,
            'media_content_type': media_content_type
        }
        
        # Se for um texto, envia para o Lex e retorna a resposta
        if str(message_type) == 'text':
            # Pega a resposta do Lex
            lex_response = lex_client.recognize_text(
                botId=os.environ['LEX_BOT_ID'],
                botAliasId=os.environ['LEX_BOT_ALIAS_ID'],
                localeId='pt_BR',
                sessionId=guest_number[10:],
                text=message_body
            )
            
            lex_message = lex_response['messages'][0]['content']
            
            # Verifica se do Lex detectou uma funcionalidade
            if lex_message in ['remedio', 'documento']:
                data['functionality'] = lex_message
                return {
                    'statusCode': 200,
                    'body': f'Ok. Envie a imagem do {data["functionality"]}'
                }
                
            # Caso não detecte, envia a mensagem para o Lex responder
            else:
                # Manda o áudio
                sendAudioMessage(lex_message, guest_number, s3_client, twilio_client, my_number)
                
                return {
                    'statusCode': 200,
                    'body': lex_message
                }
                
        # Verifica se a mensagem contém uma imagem
        elif int(num_media) > 0 and 'image' in str(media_content_type):
            
            # Pega a funcionalidade de acordo com a ultima mensagem enviada
            data['functionality'] = get_last_message_sent_to_user(data)
            
            if data['functionality'] in ['remedio', 'documento']:
                print(f"Funcionality: {data['functionality']}")
                
                # Salva a imagem no bucket e retorna suas informações
                payload = imagePrincipal(data)
                
                # Informações da solicitação
                message_infos = {
                    'data': data,
                    'payload': payload
                }
                
                # Envia a mensagem para a fila do SQS
                send_message_to_sqs(message_infos)
                
                print("Mensagem enviada para a fila do SQS.")
                
                return {
                    'statusCode': 200,
                    'body': 'Aguarde um momento enquanto processamos sua solicitação.'
                }
                
            else:
                return {
                    'statusCode': 200,
                    'body': 'Não entendi, antes informe a funcionalidade que deseja utilizar.'
                }
                
        
        else:
            return {
                'statusCode': 200,
                'body': 'Tipo de conteúdo não suportado, utilize apenas texto ou imagens.'
            }
    
    except (BotoCoreError, ClientError) as error:
        print(f"Error: {error}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(error)})
        }
    except Exception as e:
        print(f"Exception: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }
