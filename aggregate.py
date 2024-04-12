import pandas as pd
import numpy as np

from agg_funksjoner import agg_stats

from funksjoner import create_client, write_to_BQ

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'
DATASET = 'teamkatalogen'
kilde_tabell = 'teamkat_gender_pred'

# Create BigQuery client
bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

# Read data from BigQuery
sql_src_qry = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.{kilde_tabell}`"

df = bq_client.query(sql_src_qry).to_dataframe()
df.replace({np.nan: None}, inplace = True)

# Process data
df['dato_mnd'] = pd.to_datetime(df['dato_mnd'], format='%Y-%m-%d')
datelist = df.dato_mnd.unique()

cols_omraade_rolle = ['dato_mnd', 'Omraade', 'Rolle', 'antall_totalt', 'antall_kvinner', 'antall_ukjent']
cols_rolle = ['dato_mnd', 'Rolle', 'antall_totalt', 'antall_kvinner', 'antall_ukjent']
cols_omraade = ['dato_mnd', 'Omraade', 'antall_totalt', 'antall_kvinner', 'antall_ukjent']

df_list_omraade_rolle = []
df_list_rolle = []
df_list_omraade = []

roller_list = np.unique(sum(df['Roller'].str.split(', ').dropna().to_numpy(), []))

for mnd in datelist:
    df_mnd = df[df['dato_mnd'] == mnd]
    #regner ut områdeandel per måned
    df_mnd_omraade_stats = agg_stats(df_mnd)
    df_mnd_omraade_stats['dato_mnd'] = mnd
    df_list_omraade.append(df_mnd_omraade_stats)

    for rolle in roller_list: #man kan ha flere roller
        df_rolle_mnd = df_mnd[df_mnd["Roller"].str.contains(rolle, na=False)]
        df_rolle_mnd['Rolle'] = rolle
        df_rolle_mnd = df_rolle_mnd.groupby(["dato_mnd","Rolle","Omraade", "gender_pred"]).size().reset_index(name='Antall')
        df_list_omraade_rolle.append(df_rolle_mnd)


df_mnd_total = pd.concat(df_list_omraade)
df_mnd_total.rename(columns={'Total': 'antall_totalt', 'sum_kvinner': 'antall_kvinner','sum_ukjent': 'antall_ukjent'}, inplace=True)
df_mnd_total = df_mnd_total[cols_omraade]


df_rolle_omraadeT = pd.concat(df_list_omraade_rolle)
df_rolle_omraade = df_rolle_omraadeT.pivot(index = ['dato_mnd','Rolle', 'Omraade'],columns = 'gender_pred',values = 'Antall').reset_index().fillna(0)
df_rolle_omraade['Total'] = df_rolle_omraade['female']+ df_rolle_omraade['male']+ df_rolle_omraade['unknown']
df_rolle_omraade.rename(columns={'Total': 'antall_totalt', 'female': 'antall_kvinner','unknown': 'antall_ukjent'}, inplace=True)
df_rolle_omraade = df_rolle_omraade[cols_omraade_rolle]

df_rolle = df_rolle_omraadeT.groupby(["dato_mnd", "Rolle", "gender_pred"]).sum("Antall").reset_index()
df_rolle = df_rolle.pivot(index = ['dato_mnd','Rolle'],columns = 'gender_pred',values = 'Antall').reset_index().fillna(0)
df_rolle['Total'] = df_rolle['female']+ df_rolle['male']+ df_rolle['unknown']
df_rolle.rename(columns={'Total': 'antall_totalt', 'female': 'antall_kvinner','unknown': 'antall_ukjent'}, inplace=True)
df_rolle = df_rolle[cols_rolle]

#writing to BQ
write_to_BQ(client=bq_client, table_name="omraade_rolle_stats", dframe=df_rolle_omraade, dataset=DATASET, disp = "WRITE_TRUNCATE")
write_to_BQ(client=bq_client, table_name="omraade_stats", dframe=df_mnd_total, dataset=DATASET, disp = "WRITE_TRUNCATE")
write_to_BQ(client=bq_client, table_name="rolle_stats", dframe=df_rolle, dataset=DATASET, disp = "WRITE_TRUNCATE")

