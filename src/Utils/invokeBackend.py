import boto3, json

def invokeBackend(data, payload):

    # Inicializa o cliente da Lambda
    lambda_client = boto3.client('lambda')
        
    # Lista as Lambdas
    list_lambdas = lambda_client.list_functions()

    # Busca o ARN da Lambda de reconhecimento de imagem
    for function in list_lambdas['Functions']:
        if function['FunctionName'] == 'AcessibilityService-dev-backendHandler':
            function_arn = function['FunctionArn']
            break
    
    # Log no CloudWatch
    print("Invocando Lambda do Backend...")
    
    lambda_response = lambda_client.invoke(
        FunctionName=function_arn,
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "data": data,
            "payload": payload
        })
    )
    
    print(f"Resposta da Lambda do backend: {lambda_response}")
    
    return lambda_response