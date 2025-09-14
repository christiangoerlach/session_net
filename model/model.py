import os
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceAdministrationClient
from azure.ai.documentintelligence.models import BuildDocumentModelRequest
from azure.core.credentials import AzureKeyCredential

# Lade Umgebungsvariablen aus config.env
load_dotenv('../config.env')

endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT')
key = os.getenv('DOCUMENTINTELLIGENCE_API_KEY')
blob_container_url = os.getenv('BLOBSASURL')

client = DocumentIntelligenceAdministrationClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# Erstelle Build Request
build_request = BuildDocumentModelRequest(
    model_id="protokoll-analyse-modell",
    build_mode="neural",
    azure_blob_source={
        "containerUrl": blob_container_url
    }
)

poller = client.begin_build_document_model(body=build_request)

model = poller.result()
print(f"Modell-ID: {model.model_id}")
