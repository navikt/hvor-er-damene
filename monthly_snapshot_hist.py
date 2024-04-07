import os
import pandas as pd
import json
from datetime import datetime

from funksjoner import create_client, get_teamkatalogen_data, write_to_BQ

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'
DATASET = 'teamkatalogen'

files = os.listdir('hist_data')

# Create BigQuery client

bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

for file in files:
    print(file)
    print(len(file))
    df = pd.read_excel('hist_data/' + file)
    if len(file) == 22:
        dato = '01' + file[14:17] + '23'
        df['lastet_dato'] = datetime.strptime(dato, '%d%b%y')
    else:
        dato = '01' + file[14:17] + '24'
        df['lastet_dato'] = datetime.strptime(dato, '%d%b%y')
    df.rename(columns={'Område': 'Omraade'}, inplace=True)
    write_to_BQ(client=bq_client, table_name="monthly_snapshot_raw", dframe=df, dataset=DATASET)
    print(df.__len__())