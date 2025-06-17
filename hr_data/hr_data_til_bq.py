"""
daglig DAG for speiling av hr-tabell fra oracle til bigquery

laster data fra Oracle onprem til BQ
"""

import json
import logging
import os

import oracledb
import pandas as pd
from google.cloud import secretmanager
from google.cloud.bigquery import Client, LoadJobConfig

logging.basicConfig(level=logging.INFO)

sql = "select * from dt_hr.hrres_ressurs_sommer"

# hente secret fra Google Secret Manager
secret_name = "dvh_srv_team_heda_py"
logging.info(f"Setter miljøvariabl-hemmeligheter fra: {secret_name}")
full_secret_name = f"projects/847673271220/secrets/{secret_name}/versions/latest"
client = secretmanager.SecretManagerServiceClient()
response = client.access_secret_version(request={"name": full_secret_name})
secret = json.loads(response.payload.data.decode("UTF-8"))

os.environ["DB_HOST"] = secret["DB_HOST"]
os.environ["DB_PORT"] = secret["DB_PORT"]
os.environ["DB_USER"] = secret["DB_USER"]
os.environ["DB_PASSWORD"] = secret["DB_PASSWORD"]
os.environ["DB_SERVICE_NAME"] = secret["DB_SERVICE_NAME"]

logging.info(
    f"Secrets for {os.environ['DB_USER']} mot {os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_SERVICE_NAME']}"
)


# koble til Oracle og kjøre spørring
connection = oracledb.connect(
    port=os.environ["DB_PORT"],
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    service_name=os.environ["DB_SERVICE_NAME"],
)

with connection.cursor() as cursor:
    cursor.execute(sql)
    columns = [col[0].lower() for col in cursor.description]
    data = cursor.fetchall()
df_ansatte = pd.DataFrame(data, columns=columns)
logging.info(f"Hentet {len(df_ansatte)} rader")
connection.close()

# laste data til BQ
client = Client(project="heda-prod-2664")
job_config = LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",
    create_disposition="CREATE_IF_NEEDED",
)
bq_dataset = "heda-prod-2664.hr_data"
bq_table = f"{bq_dataset}.ansatte_direktoratet_raw"

run_job = client.load_table_from_dataframe(df_ansatte, bq_table, job_config=job_config)
run_job.result()
