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
    df_søkere = pd.read_excel('../data/antall søkere på utvikler-stillinger IT 2017-2024.xlsx',
                       sheet_name='Søkere på stillinger',
                       header=7)

    df_ansatt = pd.read_excel('../data/antall søkere på utvikler-stillinger IT 2017-2024.xlsx',
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

    fig = px.scatter(df_stillinger, x="Søknadsfrist", y=["kvinneandel_søkere", "kvinneandel_ansatt"],
                     size="Antall stillinger",
                     hover_data=["Stillingsnummer", "Total_ansatt", "Total_søkere", "Stillingstittel i annonse"],
                     labels={"value": "Kvinneandel", "variable": ""},
                     color_discrete_sequence = colours,)
    return fig
#%%
if __name__ == "__main__":
    #%%
    [df_søkere, df_ansatt] = _get_stilling_data()

    df_søkere = df_søkere.sort_values(by=["Stillingsnummer", "Total"])
    df_søkere = df_søkere.drop_duplicates(['Stillingsnummer'], keep='last')
    df_stillinger = df_søkere.merge(df_ansatt[["Stillingsnummer","Publisering til","Total","Kvinne"]], on = "Stillingsnummer", how = "left", suffixes=('_søkere', '_ansatt'))
    df_stillinger["Søknadsfrist"].fillna(df_stillinger["Publisering til"], inplace = True)
    df_stillinger["kvinneandel_søkere"] = round(df_stillinger["Kvinne_søkere"]/df_stillinger["Total_søkere"]*100,2)
    df_stillinger["kvinneandel_ansatt"] = round(df_stillinger["Kvinne_ansatt"]/df_stillinger["Total_ansatt"]*100,2)
    df_stillinger['Søknadsfrist'] = pd.to_datetime(df_stillinger['Søknadsfrist'], format='%d.%m.%Y')
    #%%
    print(df_stillinger.head(5))
    ## aggregate df_Stillinger to quarterly data for kvinne_Ansatt og totalt_ansatt and create a dataframe 

    df_agg = df_stillinger.groupby(pd.Grouper(key='Søknadsfrist', freq='Q')).agg({'Total_ansatt': 'sum', 'Kvinne_ansatt': 'sum'}).reset_index()
    df_agg['andel'] = df_agg['Kvinne_ansatt']/df_agg['Total_ansatt']*100
    df_agg.head()

    #%%
    fig = px.bar(df_agg, x="Søknadsfrist", y=["Kvinne_ansatt", "Total_ansatt"])
    ## change this to percentages
    fig_pers = px.bar(df_agg, x="Søknadsfrist", y=["andel"], barmode='group')
    fig_pers.show()



    fig.show()
    ## plot the persentage og Kvinne_ansatt og the Total_Ansatt
    
# %%
