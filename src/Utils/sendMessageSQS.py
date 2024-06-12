import boto3, json

def send_message_to_sqs(message_infos):
    sqs = boto3.client('sqs')

    # Pega a URL da fila
    response = sqs.get_queue_url(QueueName='luz-guia')
    queue_url = response['QueueUrl']
    
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_infos)
    )