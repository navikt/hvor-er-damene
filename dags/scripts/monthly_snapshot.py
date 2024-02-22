import pandas as pd

def get_teamkatalogen_data():
    url = 'https://teamkatalog-api.intern.nav.no/member/export/ALL'
    df = pd.read_excel(url)
    return df

def main():
    df = get_teamkatalogen_data()
    print(df.head())

if __name__ == '__main__':
    main()