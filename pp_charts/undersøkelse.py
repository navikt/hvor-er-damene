
import plotly.express as px
from bucket_functions import read_heda_bucket

df = read_heda_bucket(bucket_name = 'undersokelse', file_name = 'spørreundersøkelse_ud_23.csv')
#df = pd.read_csv("../../GitHub/teamkat-hist/data/Spørre2.csv", sep =";")

#get values in data frame not nan
svar_utdyp = df[df["Er det noe du vil utdype?"].notna()][['Kjønn','Alder', 'Seksjon', 'Er det noe du vil utdype?']]

colours_NAV = ['#3386E0', #blue-400
                '#005B82', #Deepblue-500
                '#6AA379',  # Green-200
                '#368DA8', #Lightblue-700
                '#C77300', #Orange-600
                '#8269A2']#Purple-400

colours_NAV.reverse()

colours = ['#8269A2', #Purple-400
        '#3386E0', #blue-400
        '#005B82',#deepblue
        '#C77300', #Orange-600
        '#6AA399', #turkis
]

def make_andel_bar_chart(df, xvalue = "", yvalue = "Jeg trives i jobben min", facet_color = ""):
    df = df[df["Kjønn"].isin(["Kvinne", "Mann"])]
    if facet_color == "":
        df = df[df["Seksjon"].isin(["utvikling"])]
        df = df.groupby(["Kjønn",yvalue]).size().reset_index(name='Antall')
        df["Andel"]=df.groupby(["Kjønn"])["Antall"].apply(lambda x: x / x.sum()).reset_index()["Antall"]
    else:
        df = df.groupby(["Kjønn", yvalue, facet_color]).size().reset_index(name='Antall')
        df["Andel"] = df.groupby(["Kjønn", facet_color])["Antall"].apply(lambda x: x / x.sum())
    df["Andel"] = (100*df["Andel"]).round(1)
    #df = df[df[yvalue].isin(["Ja"])]

    fig = px.bar(df, x="Kjønn", y="Andel", color=yvalue,
                 barmode='group',
                 color_discrete_sequence = colours,
                 #text = "Andel",
                 #title= yvalue,
                 #facet_col=facet_color,
                 #category_orders={"Alder": ["Under 30", "30+"]},
                 labels={yvalue: "", "Andel":"Prosent", "Kjønn": ""}
                 #category_orders= {yvalue: ["Ofte", "Aldri", "Det har skjedd"]},
                 )
    fig.update_layout( plot_bgcolor='#C0B2D2',
                        paper_bgcolor= 'rgba(0,0,0,0)',
                       font_size = 30,
                       )
    fig.show()


#make_andel_bar_chart(df, yvalue = 'Jeg trives i jobben min')
#make_andel_bar_chart(df, yvalue = 'Jeg har opplevd at min tekniske kompetanse blir undervurdert (av meg selv eller andre)',
#                     facet_color = "")
#make_andel_bar_chart(df, yvalue = 'Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg',
#                     facet_color = "")
make_andel_bar_chart(df, yvalue = 'Jeg savner flere  kvinnelige tekniske rollemodeller i NAV IT', facet_color="")
#make_andel_bar_chart(df, yvalue = 'Jeg er fornøyd med kjønnsbalansen i avdelingen (Utvikling og Data)')
#make_andel_bar_chart(df, yvalue = 'Det er mer vi bør gjøre for å utligne kjønnsforskjellene')

#make_andel_bar_chart(df, yvalue = 'Jeg elsker å kode/programmere utenfor arbeidstid', facet_color="Seksjon")
