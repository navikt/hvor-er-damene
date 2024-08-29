
import plotly.express as px
from bucket_functions import read_heda_bucket
lys_lilla = '#DEC3FF'#'rgb(222, 195, 255)'#
minty= '#43B6A5'#'rgb(67, 182, 165)'#
dus_blå ='#6488EA' #'rgb(100, 136, 234)'

df = read_heda_bucket(bucket_name = 'undersokelse', file_name = 'spørreundersøkelse_ud_23.csv')


def kakediagram(df, kjonn, navn, vis_legend, yvalue, col_map={'Ja':minty,
                    'Nei': lys_lilla}, category_orders={}):
    df2 = df.groupby(["Kjønn", yvalue]).size().reset_index(name='Antall')
    df2["Andel"] = df2.groupby(["Kjønn"])["Antall"].apply(lambda x: x / x.sum()).reset_index()["Antall"]
    df2["Andel"] = round(df2["Andel"],3)
    df2 = df2.rename(columns={yvalue: 'variabel'})
    df2 = df2[df2['Kjønn'] == kjonn]
    fig = px.pie(values=df2['Andel'],
                 names=df2['variabel'],
                 color=df2['variabel'],
                 color_discrete_map= col_map,
                 category_orders=category_orders,
                 )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=vis_legend
    )
    fig.update_traces(sort=False)
    fig.update_traces(showlegend=False, textinfo='none',)

    # save as svg
    fig.write_image(f"figurer_javazone/{navn}_{kjonn}.svg")
    #fig.show()

df = df[df["Kjønn"].isin(["Kvinne", "Mann"])]
df = df[df["Seksjon"].isin(["utvikling"])]

#rollemodeller


kakediagram(df, 'Kvinne','rollemodeller_nav', vis_legend = False,
            yvalue = 'Jeg savner flere  kvinnelige tekniske rollemodeller i NAV IT')
kakediagram(df, 'Mann','rollemodeller_nav', vis_legend = False,
            yvalue = 'Jeg savner flere  kvinnelige tekniske rollemodeller i NAV IT')

#teknisk kompetanse
kakediagram(df, 'Kvinne','teknisk_kompetanse_nav',
            vis_legend = False,
            yvalue='Jeg har opplevd at min tekniske kompetanse blir undervurdert (av meg selv eller andre)',
            col_map={'Ofte': minty,
                     'Aldri': lys_lilla,
                     'Det har skjedd': dus_blå},
            category_orders={'Ofte': '1',
                     'Aldri': '2',
                     'Det har skjedd': '3'}
)
kakediagram(df, 'Mann','teknisk_kompetanse_nav',
            vis_legend = False,
            yvalue='Jeg har opplevd at min tekniske kompetanse blir undervurdert (av meg selv eller andre)',
            col_map={'Ofte': minty,
                     'Aldri': lys_lilla,
                     'Det har skjedd': dus_blå},
            category_orders={'Ofte': '1',
                             'Aldri': '2',
                             'Det har skjedd': '3'}
            )

#normer_og_forventninger

kakediagram(df, 'Kvinne','normer_og_forventninger_nav', vis_legend = False,
            yvalue='Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg',
            col_map={'Ja det har jeg følt': minty,
                     'Nei det har jeg ikke følt': lys_lilla,
                     'Vet ikke': dus_blå}
            ,
            )
kakediagram(df, 'Mann','normer_og_forventninger_nav', vis_legend = False,
            yvalue='Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg',
            col_map={'Ja det har jeg følt': minty,
                     'Nei det har jeg ikke følt': lys_lilla,
                     'Vet ikke': dus_blå},
            )