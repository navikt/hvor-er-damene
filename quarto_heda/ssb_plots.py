# Post spørring og få Pandas dataframe i retur
# benytter biblioteket pyjstat for JSON-stat
import plotly.express as px
import pandas as pd
from pyjstat import pyjstat
import requests

colours = ['#8269A2', #Purple-400
        '#3386E0', #blue-400
        '#005B82',#deepblue
        '#C77300', #Orange-600
        '#6AA399', #turkis
]

def _get_data_api():
    # Arbeidsforhold
    POST_URL = "https://data.ssb.no/api/v0/no/table/13352"

    # API spørring, filtrer på alder, kjønn og yrke = IKT-Rådgivere
    payload = {"query": [
        {
          "code": "Alder",
          "selection": {
            "filter": "item",
            "values": [
              "999D",
              "0-39",
              "40-54",
              "55+"
            ]
          }
        },
        {
          "code": "Kjonn",
          "selection": {
            "filter": "item",
            "values": [
              "0",
              "1",
              "2"
            ]
          }
        },
        {
          "code": "Yrke",
          "selection": {
            "filter": "vs:NYK08yrkeregsys3",
            "values": [
              "251"
            ]
          }
        },
        {
          "code": "ContentsCode",
          "selection": {
            "filter": "item",
            "values": [
              "Lonsstakere"
            ]
          }
        }
      ],
      "response": {
        "format": "json-stat2"
      }
    }

    resultat = requests.post(POST_URL, json = payload)
    # Resultat gir bare http statuskode - 200 hvis OK. Body ligger i resultat.text
    # print(resultat)

    dataset = pyjstat.Dataset.read(resultat.text)
    df = dataset.write('dataframe')
    return df



def make_ssb_yrke_plot():
    df = _get_data_api()
    df = df.pivot(index=['kvartal', 'alder'], columns='kjønn', values='value').reset_index().fillna(0)
    df['kvinneandel'] = round(df['Kvinner'] / (df['Begge kjønn']) * 100,2)
    df = df[df['kvartal'].str.endswith('K1')]

    fig = px.line(df, x = 'kvartal', y = 'kvinneandel', color = "alder",
                  markers = True,
                  color_discrete_sequence = colours,
                  category_orders= {"alder": ["Under 40 år", "40-54 år", "55 år eller eldre", "Alle aldre"]},
                  labels={"kvartal": "", "alder": "", "kvinneandel": ""},)
    fig['data'][3]['line']['width'] = 5


    return fig

def make_sopptak_chart():
    data = {'År':list(range(2005, 2025)) ,
            'Kvinneandel tilbud':[17.5,
            22.5,
            21.3,
            22.0,
            17.5,
            20.5,
            20.9,
            19.4,
            20.1,
            20.4,
            21.8,
            23.1,
            25.6,
            26.8,
            28.9,
            31.3,
            32.5,
            34.1,
            37.1,
            38.0]
            }

    # Create DataFrame
    df = pd.DataFrame(data)
    #make a line chart of df
    fig = px.line(df, x="År", y="Kvinneandel tilbud",
                    markers=True,

                  color_discrete_sequence=colours,
                  #title="Samordna opptak IKT studier: Andel kvinner blant tilbud om studieplass ",
                  labels={"Kvinneandel tilbud": "", "År": "", "variable": ""},
                  )
    fig.update_traces(marker = {"size": 10})
    fig.update_traces(line = {"width": 4})
    return fig

if __name__ == "__main__":
    fig = make_ssb_yrke_plot()
    fig.show()