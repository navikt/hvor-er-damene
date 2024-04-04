import pandas as pd
import json
from datetime import datetime

from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import secretmanager

PROJECT_ID = 'heda-prod-2664'
DATASET = 'teamkatalogen'
def get_secret():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/heda-access-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret = json.loads(response.payload.data.decode('UTF-8'))
    return secret
def create_client():
    key = get_secret()
    creds = service_account.Credentials.from_service_account_info(key)
    client = bigquery.Client(credentials=creds, project=creds.project_id)
    return client
def get_teamkatalogen_data():
    url = 'https://teamkatalog-api.intern.nav.no/member/export/ALL'
    df = pd.read_excel(url)
    return df

def write_to_BQ(client, table_name, table):
    with open('schema.json', 'rb') as f:
        schema = json.load(f)

    table_id = DATASET+'.'+table_name

    job_config = bigquery.LoadJobConfig(
        schema=schema[table_name],
        write_disposition = "WRITE_APPEND"
    )

    job = client.load_table_from_dataframe(
        table, table_id, job_config=job_config
    )

def main():
    # Get data from Teamkatalogen
    df = get_teamkatalogen_data()

    # Process data
    df['lastet_dato'] = datetime.today()
    df.rename(columns={'Område': 'Omraade'}, inplace=True)

    # Create BigQuery client
    BQ_client = create_client()

    # Save data to BigQuery
    write_to_BQ(BQ_client, table_name = "monthly_snapshot_raw", table = df)

if __name__ == '__main__':
    main()