import json
import pandas as pd
import plotly.express as px
from bucket_functions import read_heda_bucket
from ssb_plot import _get_data_api
from pyjstat import pyjstat
import requests

df_ssb = _get_data_api()
df_ssb = df_ssb.pivot(index=['kvartal', 'alder'], columns='kjønn', values='value').reset_index().fillna(0)
df_ssb['Under 40 år'] = round(df_ssb['Kvinner'] / (df_ssb['Begge kjønn']) * 100, 2)
df_ssb = df_ssb[df_ssb['kvartal'].str.endswith('K1')]
df_ssb['år'] = df_ssb['kvartal'].str.slice(0, 4).astype('int64')
df_ssb = df_ssb[df_ssb['alder'].isin(["Under 40 år"])]

df = read_heda_bucket(bucket_name = 'samordna_opptak', file_name = 'samordna_opptak_ikt.csv')
df['Tilbud studieplass'] = round(df['Søkere tilbud Kvinne'] / (df['Søkere tilbud Total']) * 100,1)

df=df.merge(df_ssb, left_on='År', right_on = 'år', how='outer' )

minty='#43B6A5'
lys_lilla = '#DEC3FF'
mørk_lilla='#643999'

fig = px.line(df, x="År", y=["Tilbud studieplass", "Under 40 år"],
              markers=True,
              color_discrete_sequence=[minty, lys_lilla],
              labels={"value": "", "År": "", "variable": ""},
              )

fig.update_traces(marker={"size": 10})
fig.update_traces(line={"width": 4})
fig.update_layout(plot_bgcolor=mørk_lilla,
                  paper_bgcolor='rgba(0,0,0,0)',
                  font_size=25,
                  font_color='white',
                  )


#fig.show()
fig.write_image(f"figurer_javazone/kombinert_so_ssb.svg")
