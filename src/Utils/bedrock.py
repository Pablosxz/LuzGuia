import json
import boto3
import re


# Gera o texto no bedrock 
def generateText(modelId, body):
    bedrockRuntime = boto3.client('bedrock-runtime')

    accept = "application/json"
    contentType = "application/json"
    
    try:
        # Invoca o modelo
        response = bedrockRuntime.invoke_model(
            body=body, modelId=modelId, accept=accept, contentType=contentType
        )
        responseBody = json.loads(response.get("body").read().decode('utf-8'))

        return responseBody
    except Exception as e:
        print(f"Erro no cliente Bedrock: {str(e)}")
        return None


# Recebe o nome do remédio utilizando o bedrock com base em um texto
def getMedicineName(text):
    try:
        if not text:
            return None
        modelId = 'amazon.titan-text-express-v1'
        print("Text from Rekognition: ",text)
        
        prompt = f"""{text}
            Com base nos dados acima, busque o nome do remédio, me diga apenas o nome do remédio, mais nada, nada como 'o nome do remédio é...',
            nem mesmo a quantidade de mg, apenas o remédio.
            Se não encontrar nenhum nome de remédio, apenas retorne 'None'.
            Qual o nome do remédio?"""

        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 100,
                "stopSequences": [],
                "temperature": 0,
                "topP": 0.9
            }
        })

        responseBody = generateText(modelId, body)
        res = responseBody['results'][0]['outputText']
        res = res.replace("\n", '')
        
        # Remove caracteres especiais
        res = re.sub(r'[^\w\s]', '', res)
        
        print(f"Nome do remédio: {res}")

        if "None" in res or "Digite" in res or "Citalopram" in res:
            return None
        return res

    except boto3.exceptions.Boto3Error as e:
        print(f"Erro no cliente Bedrock: {str(e)}")
        return None
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None
    

# Responde a uma pergunta com base em um texto usando o bedrock
def answerQuestion(text, question):
    try:
        modelId = 'amazon.titan-text-express-v1'
        
        prompt = f"{text}\\nCom base nesse texto, em um paragrafo, me responda, {question}"


        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 600,
                "stopSequences": [],
                "temperature": 0.1,
                "topP": 0.9
            }
        })

        responseBody = generateText(modelId, body)
        res = responseBody['results'][0]['outputText']
        return res

    except boto3.exceptions.Boto3Error as e:
        print(f"Erro no cliente Bedrock: {str(e)}")
        return None
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None


def formatText(text):
    text = text[:1600]
    # Caractere a ser encontrado
    ultima_ocorrencia = text.rfind(".")
    text = text[:ultima_ocorrencia + 1]
    texto_corrigido = re.sub(r'(?<![.:;!?])\n', ' ', text)
    return texto_corrigido