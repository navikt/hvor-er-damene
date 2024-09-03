import pandas as pd
import plotly.express as px
from bucket_functions import read_heda_bucket

df = read_heda_bucket(bucket_name = 'rekruttering', file_name = 'andre_bedrifter.csv')

df['kvinneandel']=100*df['Antall_kvinner']/df['Antall_totalt']
df = df.drop(df[(df.Bedrift.isin(['BaneNOR', 'Sopra Steria']))].index)

df['text_position'] = 'middle right'
df.loc[(((df['Bedrift'] == 'BaneNOR') | (df['Bedrift'] == 'RT08') ),
        'text_position')] = 'top left'
df.loc[(((df['Bedrift'] == 'Indoor industrial spaces') | (df['Bedrift'] == 'Amedia') ),
        'text_position')] = 'bottom right'
df.loc[(((df['Bedrift'] == '3LC.AI') | (df['Bedrift'] == 'Origo') | (df['Bedrift'] == 'Lånekassen')
         ), 'text_position')] = 'top right'


minty='#43B6A5'
lys_lilla = '#DEC3FF'
mørk_lilla='#643999'

fig = px.scatter(df, x="Antall_totalt", y="kvinneandel", text="Bedrift", size_max=60,
              color_discrete_sequence=[minty],
              labels={"kvinneandel": "Kvinneandel", "Antall_totalt": "Antall utviklere"},
              )
fig.update_layout(plot_bgcolor=mørk_lilla,
                  paper_bgcolor='rgba(0,0,0,0)',
                  font_size=45,
                  font_color='white',
                  )
fig.update_traces(textposition=df['text_position'])
fig.update_xaxes(showgrid=True, gridcolor=lys_lilla)
fig.update_yaxes(showgrid=True, gridcolor=lys_lilla)
fig.update_traces(marker={"size": 20})


fig.show()
fig.write_image(f"figurer_javazone/andre_bedrifter.svg")
