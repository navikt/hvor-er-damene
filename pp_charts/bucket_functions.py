import json
import pandas as pd

from io import StringIO, BytesIO
from google.oauth2 import service_account
from google.cloud import storage
from google.cloud import secretmanager

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'

def read_heda_bucket(bucket_name = 'samordna_opptak', file_name = 'samordna_opptak.csv'):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{SA_KEY_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret = json.loads(response.payload.data.decode('UTF-8'))

    creds = service_account.Credentials.from_service_account_info(secret)
    storage_client = storage.Client(credentials=creds, project=creds.project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    byte_stream = BytesIO()
    blob.download_to_file(byte_stream)
    byte_stream.seek(0)

    df = pd.read_csv(byte_stream, sep = ';')
    return df