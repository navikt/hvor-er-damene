import pandas as pd
import plotly.express as px
import sys
sys.path.append("..")
from funksjoner import create_client

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'
DATASET = 'teamkatalogen'

# Create BigQuery client
bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

colours = ['#8269A2', #Purple-400
        '#3386E0', #blue-400
        '#005B82',#deepblue
        '#C77300', #Orange-600
        '#6AA399', #turkis
]

def make_omraade_bar_chart(bq_table = 'omraade_stats'):
    sql_src_qry = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.{bq_table}`"

    df = bq_client.query(sql_src_qry).to_dataframe()

    df['dato_mnd'] = pd.to_datetime(df['dato_mnd'], format='%Y-%m-%d')
    df['Kvinneandel']= round(df['antall_kvinner']/df['antall_totalt'],2)*100
    df['Ukjentandel']= round(df['antall_ukjent']/df['antall_totalt'],2)*100

    max_dato = max(df['dato_mnd'])

    fig = px.bar(df[(df['dato_mnd']==max_dato) & (df['antall_totalt'] > 9)],
                 x="Omraade",
                 y=["Kvinneandel","Ukjentandel"],
                 hover_data=["antall_totalt"],
                 labels={"value": "", "variable": "", "Omraade": ""},
                 color_discrete_sequence=colours,
                 title = f"uttrekk per {max_dato}")
    fig.update_layout(xaxis={'categoryorder':'total ascending'})

    return fig

def make_roller_line_chart(bq_table = 'rolle_stats'):
    sql_src_qry = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.{bq_table}`"

    df = bq_client.query(sql_src_qry).to_dataframe()

    df['dato_mnd'] = pd.to_datetime(df['dato_mnd'], format='%Y-%m-%d')
    df = df.sort_values(by="dato_mnd")
    df['Kvinneandel']= round(df['antall_kvinner']/df['antall_totalt'],2)*100

    interessante_roller = ["Jurist", "Designer", "Data scientist", "Data engineer", "Utvikler"]
    df = df[df['Rolle'].isin(interessante_roller)]
    fig = px.line(df[df['antall_totalt'] > 9],
                   x="dato_mnd", y="Kvinneandel", color="Rolle",
                   hover_data=["antall_totalt"],
                   labels={"Kvinneandel": "", "dato_mnd": ""},
                  category_orders={"Rolle": interessante_roller},
                   markers=True)
    return fig

if __name__ == "__main__":
    fig = make_roller_line_chart()
    fig.show()