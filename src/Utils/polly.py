import boto3
import os

def pollySpeech(text):
    try:
        # Inicializa o cliente Polly
        polly = boto3.client('polly')

        # Solicitação ao Polly para sintetizar fala
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Vitoria'
        )

        return response
    
    except Exception as e:
        print(f"Erro ao sintetizar fala: {e}")
        return None


def sendAudioMessage(payload_content_body, guest_number, s3_client, twilio_client, my_number):
    # Converte a resposta do Lex em áudio
    polly_response = pollySpeech(payload_content_body)
    
    # Salva o áudio em um bucket S3
    audio_key = f"Audios/response-{guest_number[10:]}.mp3"
    audio_stream = polly_response['AudioStream']
    s3_client.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=audio_key, Body=audio_stream.read(), ContentType='audio/mpeg')
    
    # Gera a URL do áudio
    presigned_url = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': os.environ['S3_BUCKET_NAME'], 'Key': audio_key},
        ExpiresIn=360)  # URL válida por 6 minutos
    
    
    # Envia o áudio para o número do destinatário
    message = twilio_client.messages.create(
        media_url=[presigned_url], # URL do áudio
        from_=my_number,
        to=guest_number
    )