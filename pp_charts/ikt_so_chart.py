import json
import pandas as pd
import plotly.express as px
from bucket_functions import read_heda_bucket

df = read_heda_bucket(bucket_name = 'samordna_opptak', file_name = 'samordna_opptak_ikt.csv')


df['Kvinneandel tilbud'] = round(df['Søkere tilbud Kvinne'] / (df['Søkere tilbud Total']) * 100,1)

minty='#43B6A5'
lys_lilla = '#DEC3FF'
mørk_lilla='#643999'

fig = px.line(df, x="År", y="Kvinneandel tilbud",
              markers=True,
              color_discrete_sequence=[minty],
              #title="Samordna opptak IKT studier: Andel kvinner blant tilbud om studieplass ",
              labels={"Kvinneandel tilbud": "", "År": "", "variable": ""},
              )
fig.update_traces(marker={"size": 10})
fig.update_traces(line={"width": 4})
fig.update_layout(plot_bgcolor=mørk_lilla,
                  paper_bgcolor='rgba(0,0,0,0)',
                  font_size=30,
                  font_color='white',
                  )

#fig.show()
fig.write_image(f"figurer_javazone/samordna_opptak.svg")
