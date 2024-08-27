import json
import pandas as pd
import plotly.express as px
from bucket_functions import read_heda_bucket

df = read_heda_bucket(bucket_name = 'samordna_opptak', file_name = 'samordna_opptak_ikt.csv')


df['Kvinneandel tilbud'] = round(df['Søkere tilbud Kvinne'] / (df['Søkere tilbud Total']) * 100,1)
df['name']='Tilbud studieplass'

minty='#43B6A5'
lys_lilla = '#DEC3FF'
mørk_lilla='#643999'

fig = px.line(df, x="År", y="Kvinneandel tilbud", color = "name",
              markers=True,
              color_discrete_sequence=[minty],
              #title="Samordna opptak IKT studier: Andel kvinner blant tilbud om studieplass ",
              labels={"Kvinneandel tilbud": "Kvinneandel", "År": "", "name": ""},
              )
fig.update_traces(marker={"size": 10})
fig.update_traces(line={"width": 4})
fig.update_layout(plot_bgcolor=mørk_lilla,
                  paper_bgcolor='rgba(0,0,0,0)',
                  font_size=25,
                  font_color='white',
                  )
fig.update_yaxes(range=[15,40])
fig.update_layout(showlegend=False)
#fig.update_layout(legend=dict(orientation="h"))
fig.update_xaxes(range=[1960,2025])
fig.update_xaxes(tickangle=30)

#fig.show()
fig.write_image(f"figurer_javazone/samordna_opptak_hist.svg")
