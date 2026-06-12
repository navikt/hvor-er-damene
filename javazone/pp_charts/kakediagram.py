import numpy as np
import plotly_express as px

lys_lilla = '#DEC3FF'
dus_blå ='#6488EA'
gush_grønn = '#A2AC59'
minty='#43B6A5'


def kakediagram(kvinne_andel, mann_andel, tittel):
    fig = px.pie(values=[kvinne_andel, mann_andel],
                 names=['K', 'M'],
                 color_discrete_sequence=[minty, lys_lilla])
    fig.update_layout(
        font=dict(
            size=40,
            color="white"
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    fig.update_traces(insidetextfont=dict(color='white'),
                      outsidetextfont=dict(color='white'))
    fig.update_traces(showlegend=False, textinfo='none', )
    # save as svg
    fig.write_image(f"figurer_javazone/{tittel}.svg")

kakediagram(32, 68, 'andel_IT')
kakediagram(19, 81, 'andel_u&d')
kakediagram(15, 85, 'andel_utvikler')
kakediagram(26, 74, 'andel_junior_utvikler')
kakediagram(9, 81, 'andel_senior_utvikler')
kakediagram(14, 86, 'andel_inkl_konsulent')
kakediagram(8, 92, 'andel_security_champion')
kakediagram(7, 93, 'andel_techlead')
kakediagram(0, 100, 'andel_nais')
kakediagram(0, 100, 'andel_teknologiprinsipal')

