
import plotly.express as px
from bucket_functions import read_heda_bucket
lys_lilla = '#DEC3FF'
minty='#43B6A5'
dus_blå = '#A2AC59'

df = read_heda_bucket(bucket_name = 'undersokelse', file_name = 'spørreundersøkelse_ud_23.csv')


def kakediagram(df, kjonn, navn, vis_legend):
    df = df[df['Kjønn'] == kjonn]
    df = df.sort_values(by = 'variabel')
    fig = px.pie(values=df['Andel'],
                 names=df['variabel'],
                 color_discrete_sequence=[minty,lys_lilla, dus_blå,],
                 title = kjonn
    fig.update_layout(
        font=dict(
            size=40,
            color="white"
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=vis_legend
    )
    fig.update_traces(insidetextfont=dict(color='white'),
                      outsidetextfont=dict(color='white'))
    # save as svg
    fig.write_image(f"figurer_javazone/{navn}_{kjonn}.svg")
    #fig.show()

df = df[df["Kjønn"].isin(["Kvinne", "Mann"])]
df = df[df["Seksjon"].isin(["utvikling"])]

#rollemodeller
yvalue = 'Jeg savner flere  kvinnelige tekniske rollemodeller i NAV IT'
df1 = df.groupby(["Kjønn", yvalue]).size().reset_index(name='Antall')
df1["Andel"] = df1.groupby(["Kjønn"])["Antall"].apply(lambda x: x / x.sum()).reset_index()["Antall"]
df1 = df1.rename(columns={yvalue: 'variabel'})

#kakediagram(df1, 'Kvinne','rollemodeller_nav', vis_legend = False)
#kakediagram(df1, 'Mann','rollemodeller_nav', vis_legend = True)

#teknisk kompetanse
yvalue = 'Jeg har opplevd at min tekniske kompetanse blir undervurdert (av meg selv eller andre)'
df2 = df.groupby(["Kjønn", yvalue]).size().reset_index(name='Antall')
df2["Andel"] = df2.groupby(["Kjønn"])["Antall"].apply(lambda x: x / x.sum()).reset_index()["Antall"]
df2 = df2.rename(columns={yvalue: 'variabel'})

kakediagram(df2, 'Kvinne','teknisk_kompetanse_nav', vis_legend = False)
#kakediagram(df2, 'Mann','teknisk_kompetanse_nav', vis_legend = True)

#normer_og_forventninger
yvalue = 'Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg'
df3 = df.groupby(["Kjønn", yvalue]).size().reset_index(name='Antall')
df3["Andel"] = df3.groupby(["Kjønn"])["Antall"].apply(lambda x: x / x.sum()).reset_index()["Antall"]
df3 = df3.rename(columns={yvalue: 'variabel'})

#kakediagram(df3, 'Kvinne','normer_og_forventninger_nav', vis_legend = False)
#kakediagram(df3, 'Mann','normer_og_forventninger_nav', vis_legend = True)


#make_andel_bar_chart(df, yvalue = 'Jeg trives i jobben min')
#make_andel_bar_chart(df, yvalue = 'Jeg har opplevd at min tekniske kompetanse blir undervurdert (av meg selv eller andre)',
#                     facet_color = "")
#make_andel_bar_chart(df, yvalue = 'Jeg har følt at jeg har gått i mot normer og forventninger når det gjelder mine studie- og/eller karrierevalg',
#                     facet_color = "")
#make_andel_bar_chart(df, yvalue = 'Jeg savner flere  kvinnelige tekniske rollemodeller i NAV IT', facet_color="")
#make_andel_bar_chart(df, yvalue = 'Jeg er fornøyd med kjønnsbalansen i avdelingen (Utvikling og Data)')
#make_andel_bar_chart(df, yvalue = 'Det er mer vi bør gjøre for å utligne kjønnsforskjellene')

#make_andel_bar_chart(df, yvalue = 'Jeg elsker å kode/programmere utenfor arbeidstid', facet_color="Seksjon")
