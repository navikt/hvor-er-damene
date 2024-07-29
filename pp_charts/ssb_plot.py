import plotly.express as px
import pandas as pd
from pyjstat import pyjstat
import requests

minty='#43B6A5'
lys_lilla = '#DEC3FF'
mørk_lilla='#643999'

def _get_data_api_aku():
    # Arbeidsforhold
    POST_URL = "https://data.ssb.no/api/v0/no/table/09792"

    # API spørring, filtrer på alder, kjønn og yrke = IKT-Rådgivere
    payload = {
              "query": [
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
                    "filter": "item",
                    "values": [
                      "2512",
                      "2519"
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

    fig = px.line(df[df['alder']=="Alle aldre"], x = 'kvartal', y = 'kvinneandel', color = "alder",
                  markers = True,
                  color_discrete_sequence = [minty],
                  labels={"år": "", "alder": "", "kvinneandel": ""},)
    fig.update_traces(marker={"size": 10})
    fig.update_traces(line={"width": 4})
    fig.update_layout(plot_bgcolor=mørk_lilla,
                      paper_bgcolor='rgba(0,0,0,0)',
                      font_size=30,
                      font_color='white',
                      )

    return fig


def make_ssb_yrke_plot_aku():
    df = _get_data_api_aku()
    df = df.groupby(by=['kjønn', 'år'], as_index=False).value.sum()
    df = df.pivot(index=['år'], columns=['kjønn'], values='value').reset_index().fillna(0)
    df['kvinneandel'] = round(df['Kvinner'] / (df['Begge kjønn']) * 100,2)

    fig = px.line(df, x = 'år', y = 'kvinneandel',
                  markers = True,
                  color_discrete_sequence = colours,
                  labels={"år": "", "kvinneandel": ""},)
    return fig

if __name__ == "__main__":
    fig = make_ssb_yrke_plot()
    fig.show()