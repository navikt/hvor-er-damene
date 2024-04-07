import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

def agg_stats(dff):
    område_count = dff.groupby(["Omraade", "gender_pred"]).size().reset_index(name='Antall')
    område_count['Total'] = område_count['Antall'].groupby(område_count['Omraade']).transform('sum')

    #regner ut kvinneandel
    område_fem_count = område_count[område_count['gender_pred'] == 'female']
    område_fem_count['sum_kvinner'] = område_fem_count['Antall'].groupby(område_fem_count['Omraade']).transform('sum')
    område_fem_count = område_fem_count[['Omraade', 'sum_kvinner']].drop_duplicates()
    område_count = område_count.merge(område_fem_count, how='left', on="Omraade")

    #regner ut ukjentandel
    område_uk_count = område_count[område_count['gender_pred'] == 'unknown']
    område_uk_count['sum_ukjent'] = område_uk_count['Antall'].groupby(område_uk_count['Omraade']).transform('sum')
    område_uk_count = område_uk_count[['Omraade', 'sum_ukjent']].drop_duplicates()
    område_count = område_count.merge(område_uk_count, how='left', on="Omraade")

    område_count['Kvinneandel'] = round(100 * område_count['sum_kvinner'] / område_count['Total'], 1)
    område_count['Ukjentandel'] = round(100 * område_count['sum_ukjent'] / område_count['Total'], 1)
    område_count.fillna(0, inplace=True)
    område_count = område_count[["Omraade", "Total", "sum_kvinner", "sum_ukjent", "Kvinneandel", 'Ukjentandel']].drop_duplicates()

    return område_count