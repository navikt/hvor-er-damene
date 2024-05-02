import pandas as pd
import json

from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import secretmanager


def _get_secret(project_id, sa_key_name='heda-access-key'):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{sa_key_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret = json.loads(response.payload.data.decode('UTF-8'))
    return secret
def create_client(project_id, sa_key_name):
    key = _get_secret(project_id, sa_key_name)
    creds = service_account.Credentials.from_service_account_info(key)
    client = bigquery.Client(credentials=creds, project=creds.project_id)
    return client
def get_teamkatalogen_data():
    url = 'https://teamkatalog-api.intern.nav.no/member/export/ALL'
    df = pd.read_excel(url)
    return df

def write_to_BQ(client, table_name, dframe, dataset='teamkatalogen', disp = "WRITE_APPEND"):
    with open('schema.json', 'rb') as f:
        schema = json.load(f)

    table_id = dataset+'.'+table_name

    job_config = bigquery.LoadJobConfig(
        schema=schema[table_name],
        write_disposition = disp
    )

    job = client.load_table_from_dataframe(
        dframe, table_id, job_config=job_config
    )