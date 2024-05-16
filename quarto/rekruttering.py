#%%
import pandas as pd
import plotly.express as px
colours = ['#8269A2', #Purple-400
        '#3386E0', #blue-400
        '#005B82',#deepblue
        '#C77300', #Orange-600
        '#6AA399', #turkis
]
#%%
def _get_stilling_data():
    df_søkere = pd.read_excel('data/antall søkere på utvikler-stillinger IT 2017-2024.xlsx',
                       sheet_name='Søkere på stillinger',
                       header=7)

    df_ansatt = pd.read_excel('data/antall søkere på utvikler-stillinger IT 2017-2024.xlsx',
                       sheet_name='Ansatte på stillinger',
                       header=7)
    return df_søkere, df_ansatt

def make_stilling_plot():
    [df_søkere, df_ansatt] = _get_stilling_data()

    df_søkere = df_søkere.sort_values(by=["Stillingsnummer", "Total"])
    df_søkere = df_søkere.drop_duplicates(['Stillingsnummer'], keep='last')
    df_stillinger = df_søkere.merge(df_ansatt[["Stillingsnummer","Publisering til","Total","Kvinne"]], on = "Stillingsnummer", how = "left", suffixes=('_søkere', '_ansatt'))
    df_stillinger["Søknadsfrist"].fillna(df_stillinger["Publisering til"], inplace = True)
    df_stillinger["kvinneandel_søkere"] = round(df_stillinger["Kvinne_søkere"]/df_stillinger["Total_søkere"]*100,2)
    df_stillinger["kvinneandel_ansatt"] = round(df_stillinger["Kvinne_ansatt"]/df_stillinger["Total_ansatt"]*100,2)
    df_stillinger['Søknadsfrist'] = pd.to_datetime(df_stillinger['Søknadsfrist'], format='%d.%m.%Y')

    ## aggregate df_Stillinger to quarterly data for kvinne_Ansatt og totalt_ansatt and create a dataframe 

    df_agg = df_stillinger.groupby(pd.Grouper(key='Søknadsfrist', freq='Q')).agg({'Total_ansatt': 'sum', 'Kvinne_ansatt': 'sum', 'Total_søkere': 'sum', 'Kvinne_søkere': 'sum'}).reset_index()
    df_agg['kvinneandel_ansatt'] = df_agg['Kvinne_ansatt']/df_agg['Total_ansatt']*100
    df_agg['kvinneandel_søkere'] = df_agg['Kvinne_søkere']/df_agg['Total_søkere']*100
    df_agg['Mann_ansatt'] = df_agg['Total_ansatt'] - df_agg['Kvinne_ansatt']


    fig = px.bar(df_agg, x="Søknadsfrist", y=["Kvinne_ansatt", "Mann_ansatt"],
                 color_discrete_sequence=colours,
                 title="Antall ansatte på utviklerstillinger i IT per kvartal",
                 labels={"value": "Antall", "Søknadsfrist": "", "variable": ""})

    ## change this to percentages
    fig_pers = px.bar(df_agg, x="Søknadsfrist", y=["kvinneandel_ansatt", "kvinneandel_søkere"],
                      barmode='group',color_discrete_sequence=colours,
                      title="Kvinneandel søknader og ansettelser til utviklerstillinger i IT per kvartal",
                      labels={"value": "Kvinneandel", "Søknadsfrist": "", "Variable": ""})
    return [fig, fig_pers]
#%%
if __name__ == "__main__":

    fig, fig_pers = make_stilling_plot()
    fig_pers.show()



    fig.show()
    ## plot the persentage og Kvinne_ansatt og the Total_Ansatt
    
# %%
