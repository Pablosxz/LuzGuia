import requests
import boto3
import os
import time
from dotenv import load_dotenv

from Utils.s3 import checkObjectExists, getPdfFromS3
from Utils.bedrock import getMedicineName, answerQuestion
from Utils.rekognition import reconhecerTexto
from Utils.textract import extractTextFromPdf, uploadTextToS3


# Envia o PDF para o S3
def uploadPdftoS3(url, fileName):
    bucketName = os.getenv('S3_BUCKET_NAME')
    response = requests.get(url)
    if response.status_code == 200:
        file = response.content
        try:
            s3 = boto3.client('s3',
              aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
              aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
              aws_session_token = os.getenv('AWS_SESSION_TOKEN')
              )
            response = s3.put_object(Body = file, Bucket = bucketName, Key = f"PDFs/{fileName}", ContentType = 'application/pdf')
            return response
        except Exception as e:
            print(f"Erro ao fazer upload do arquivo para o S3: {e}")
            return None
    return None


# Recebe os ids para fazer download do PDF da bula
def getBulaIDs(medicineName, pagina=1):
    url = 'https://bula.vercel.app/pesquisar'
    querystring = {"nome": medicineName, "pagina": pagina}
            
    # Headers para simular um navegador
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    for attempt in range(3):
        try:
            print(f"Tentativa {attempt + 1} de 3")
            response = requests.get(url, headers=headers, params=querystring, timeout=20)
            print("Status code da API:", response.status_code)
            
            # Talvez retorne erro 504 devido a um limite de requisições no servidor da API
            if response.status_code == 200:
                data = response.json()
                ids = []
                for bula in data["content"]:
                    ids.append(bula["idBulaPacienteProtegido"])
                return ids
        except requests.Timeout:
            print("Erro: A solicitação ao servidor excedeu o tempo limite.")
            return None
        except requests.RequestException as e:
            print(f"Erro na request: {e}")
            return None
        except Exception as e:
            print(f'Erro: {e}')
            return None
        
        time.sleep(5)

# Recebe o nome do medicamento e passa por todos os processos até fazer upload do PDF no S3
def getBula(medicineName):
    try:
        ids = getBulaIDs(medicineName)
        print("IDs:", ids)
        if not ids:
            print("Nenhum remédio reconhecido")
            return None

        # Tenta fazer download com base nos ids fornecidos
        for id in ids:
            try:
                url = "https://bula.vercel.app/bula"
                querystring = {"id": id}
                headers = {}
                response = requests.get(url, headers=headers, params=querystring)
                
                if response.status_code == 200:
                    data = response.json()
                    pdfUrl = data['pdf']
                    fileName = f"Bula_{medicineName}.pdf"

                    # Tenta fazer download do PDF e fazer upload pro S3
                    responseDownload = uploadPdftoS3(pdfUrl, fileName)

                    # Se o download for bem sucedido
                    if(responseDownload):
                        print('Upload bem-sucedido.')
                        return pdfUrl
                else:
                    print(f'Erro ao acessar bula com ID {id}: Status code {response.status_code}')
            except Exception as e:
                print(f'Erro: {e}')
        return None

    except Exception as e:
        print(f'Erro ao tentar acessar PDF da bula: {e}')
        return None


# Recebe a key de uma imagem e passa por todos os processos até retornar um resumo da bula
def bularioHandler(imageKey):
    load_dotenv()
    # Recebe a imagem em bytes
    image = getPdfFromS3(imageKey)
    # Recebe todos os textos na imagem
    textResponse = reconhecerTexto(image)
    if textResponse['statusCode'] == 200:
        imageText = " ".join([text['detectedText'] for text in textResponse['body']])
    else:
        print("Erro ao reconhecer texto:", textResponse['body'])
        return None

    # Identifica o nome do remédio no meio de todos os textos
    medicineName = getMedicineName(imageText)

    # Caso não exista nome de remédio no texto:
    if not medicineName:
        return None
    medicineName = medicineName.capitalize()
    text = None

    # Verifica se não existe um PDF com esse nome no S3
    if not checkObjectExists(f"PDFs/Bula_{medicineName}.pdf"):
        pdf_url=getBula(medicineName)
        if not pdf_url:
            return None

    # Verifica se não existe um TXT com esse nome no S3
    if not checkObjectExists(f"Bulastxt/Bula_{medicineName}.txt"):
        text = extractTextFromPdf(f"PDFs/Bula_{medicineName}.pdf")
        uploadTextToS3(text, f"Bula_{medicineName}.txt")
    
    # Pega o texto do S3 se não tiver passado pelo processo anterior
    if not text:
        text = getPdfFromS3(f"Bulastxt/Bula_{medicineName}.txt", 1)

    return text, f"PDFs/Bula_{medicineName}.pdf"