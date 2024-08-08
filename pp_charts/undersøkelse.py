
import plotly.express as px
from bucket_functions import read_heda_bucket
lys_lilla = '#DEC3FF'
minty='#43B6A5'
dus_blå ='#6488EA'

df = read_heda_bucket(bucket_name = 'undersokelse', file_name = 'spørreundersøkelse_ud_23.csv')


def kakediagram(df, kjonn, navn, vis_legend, yvalue, col_seq = [minty,lys_lilla] ):
    df2 = df.groupby(["Kjønn", yvalue]).size().reset_index(name='Antall')
    df2["Andel"] = df2.groupby(["Kjønn"])["Antall"].apply(lambda x: x / x.sum()).reset_index()["Antall"]
    df2["Andel"] = round(df2["Andel"],3)
    df2 = df2.rename(columns={yvalue: 'variabel'})
    df2 = df2[df2['Kjønn'] == kjonn]
    fig = px.pie(values=df2['Andel'],
                 names=df2['variabel'],
                 color_discrete_sequence= col_seq,
                 )
    fig.update_layout(
        font=dict(
            size=40,
            color="white"
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=vis_legend
    )
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
            col_seq=[minty,lys_lilla, dus_blå,],)
kakediagram(df, 'Mann','teknisk_kompetanse_nav',
            vis_legend = False,
            yvalue='Jeg har opplevd at min tekniske kompetanse blir undervurdert (av meg selv eller andre)',
            col_seq=[minty, dus_blå,lys_lilla,],
            )

#normer_og_forventninger

kakediagram(df, 'Kvinne','normer_og_forventninger_nav', vis_legend = False,
            yvalue='Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg',
            col_seq=[minty, lys_lilla, dus_blå, ],
            )
kakediagram(df, 'Mann','normer_og_forventninger_nav', vis_legend = False,
            yvalue='Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg',
            col_seq=[lys_lilla, dus_blå, minty, ],
            )