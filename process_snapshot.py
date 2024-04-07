import pandas as pd
import numpy as np
from data_clean import vaske_data

from funksjoner import create_client, write_to_BQ

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'
DATASET = 'teamkatalogen'
kilde_tabell = 'monthly_snapshot_raw'
target_tabell = 'teamkat_gender_pred'

# Create BigQuery client
bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

# Read data from BigQuery
sql_src_qry = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.{kilde_tabell}`"

df = bq_client.query(sql_src_qry).to_dataframe()
df.replace({np.nan: None}, inplace = True)

# Process data
df['lastet_dato'] = pd.to_datetime(df['lastet_dato'], format='%Y-%m-%d')
datelist = df.lastet_dato.unique()

cols = ['dato_mnd', 'Ident', 'Omraade', 'Team', 'Roller', 'Type', 'for_navn', 'gender_pred']
df_list = []
for mnd in datelist:
    df_mnd = df[df['lastet_dato'] == mnd]
    df_mnd = vaske_data(df_mnd)
    df_list.append(df_mnd)

df_mnd_total = pd.concat(df_list)
df_mnd_total.rename(columns={'lastet_dato': 'dato_mnd'}, inplace=True)
df_mnd_total = df_mnd_total[cols]

#writing to BQ
write_to_BQ(client=bq_client, table_name=target_tabell, dframe=df_mnd_total, dataset=DATASET, disp = "WRITE_TRUNCATE")

