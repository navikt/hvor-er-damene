import pandas as pd
import gender_guesser.detector as gender
from datetime import date, datetime
pd.options.mode.chained_assignment = None  # default='warn'

def vaske_data(df):
    df = get_current_employees(df)
    df_dedup = df.sort_values(by=['Omraade'], ascending=False).drop_duplicates(subset=["Epost"])
    d = gender.Detector()
    df_dedup['for_navn'] = df_dedup.Fornavn.apply(get_first_name)
    df_dedup['gender_pred'] = df_dedup.for_navn.apply(d.get_gender)
    df_dedup = set_unknown_gender(df_dedup)
    return df_dedup

def get_current_employees(df):
    df['Startdato'] = pd.to_datetime(df['Startdato'], format='%Y-%m-%d')
    df['Sluttdato'] = pd.to_datetime(df['Sluttdato'], format='%Y-%m-%d')
    df.loc[pd.isnull(df['Sluttdato']), 'Sluttdato'] = datetime(2099, 1, 1)
    df = df[(df['lastet_dato'] > df['Startdato']) & (df['lastet_dato'] < df['Sluttdato'])]
    return df

def set_unknown_gender(df):
    fnames = []
    with open('navn/female_names.txt', 'r') as f:
        for line in f:
            fnames.append(line.strip())
    mnames = []
    with open('navn/male_names.txt', 'r') as f:
        for line in f:
            mnames.append(line.strip())
    df.loc[df['for_navn'].isin(fnames), 'gender_pred'] = 'female'
    df.loc[df['for_navn'].isin(mnames), 'gender_pred'] = 'male'
    df.loc[df['gender_pred'].isin(['mostly_male','mostly_female','andy']), 'gender_pred'] = 'unknown'
    return df

def get_first_name(navn):
    fornavn = navn.split(" ")[0]
    fornavn = fornavn.split("-")[0]
    return fornavn


