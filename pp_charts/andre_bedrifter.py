import pandas as pd
import plotly.express as px

data = { 'Bedrift':     ['Bekk','Origo', 'TET digital','Telenor', 'Indoor industrial spaces', 'Amedia', 'Aidn'],
         'Antall_totalt':[345,  47,         33,         200,        9,                          75,        56],
         'Antall_kvinner':[84,  11,         12,         29,         1,                          13,        10]
}

df = pd.DataFrame(data)
df['kvinneandel']=100*df['Antall_kvinner']/df['Antall_totalt']

minty='#43B6A5'
lys_lilla = '#DEC3FF'
mørk_lilla='#643999'

fig = px.scatter(df, x="Antall_totalt", y="kvinneandel", text="Bedrift", size_max=60,
              color_discrete_sequence=[minty],
              labels={"kvinneandel": "%", "Antall_totalt": "Antall utviklere o.l"},
              )
fig.update_layout(plot_bgcolor=mørk_lilla,
                  paper_bgcolor='rgba(0,0,0,0)',
                  font_size=10,
                  font_color='white',
                  )
fig.update_traces(textposition="bottom right")
fig.update_traces(marker={"size": 10})


#fig.show()
fig.write_image(f"figurer_javazone/andre_bedrifter.svg")
