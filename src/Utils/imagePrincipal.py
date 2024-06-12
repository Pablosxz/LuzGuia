import boto3
import os
import requests
import json

from twilio.rest import Client

def imagePrincipal(data):
    
    # Extrai variáveis do dicionário
    media_url = data['media_url']
    account_sid = data['account_sid']
    auth_token = data['auth_token']
    guest_number = data['guest_number']
    my_number = data['my_number']
    
    s3_client = boto3.client('s3')
    twilio_client = Client(account_sid, auth_token)

    # Fazendo uma solicitação GET para o URL do Twilio para obter os metadados da imagem        
    response = requests.get(media_url, auth=(account_sid, auth_token))

    media_content_type = response.headers.get('Content-Type')

    # Log no CloudWatch
    print(f"Media Content-Type: {media_content_type}")

    # Verifica o tipo de conteúdo da mídia
    if 'image/jpeg' in media_content_type:
        img_ext = 'jpg'
    elif 'image/png' in media_content_type:
        img_ext = 'png'
    else:
        # Erro se o tipo não for suportado
        message = twilio_client.messages.create(
            body="Tipo de conteúdo não suportado, envie uma imagem png ou jpg.",
            from_=my_number,
            to=guest_number
        )
        
        return {
            'statusCode': 400,
            'body': 'Tipo de conteúdo de mídia não suportado (Apenas imagens com extensões jpg e png são suportados).'
        }

    # Log no CloudWatch
    print(f"Image Extension: {img_ext}")
    
    # Pega o conteúdo da imagem
    image_content = response.content
            
    try:
        # Salva a imagem no bucket S3
        s3_client.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=f'Images/{guest_number[10:]}.{img_ext}', Body=image_content)
        
        # Dados da imagem
        payload = {
            's3_bucket': os.environ['S3_BUCKET_NAME'],
            's3_key': f'Images/{guest_number[10:]}.{img_ext}',
            'my_number': my_number,
            'guest_number': guest_number
        }
        
        # retorna os dados da imagem
        return payload
        
    except Exception as e:
        print(f"Ocorreu um erro ao salvar a imagem: {str(e)}")
        return {
            'statusCode': 500,
            'body':'Ocorreu um erro, midia não recebida.'
        }