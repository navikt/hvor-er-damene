import json
import pandas as pd
import plotly.express as px
from bucket_functions import read_heda_bucket

df = read_heda_bucket(bucket_name = 'samordna_opptak', file_name = 'samordna_opptak_ikt.csv')


df['Kvinneandel tilbud'] = round(df['Søkere tilbud Kvinne'] / (df['Søkere tilbud Total']) * 100,1)

colours = ['#8269A2', #Purple-400
        '#3386E0', #blue-400
        '#005B82',#deepblue
        '#C77300', #Orange-600
        '#6AA399', #turkis
]

fig = px.line(df, x="År", y="Kvinneandel tilbud",
              markers=True,
              color_discrete_sequence=colours,
              title="Samordna opptak IKT studier: Andel kvinner blant tilbud om studieplass ",
              labels={"Kvinneandel tilbud": "", "År": "", "variable": ""},
              )
fig.update_traces(marker={"size": 10})
fig.update_traces(line={"width": 4})

fig.show()
