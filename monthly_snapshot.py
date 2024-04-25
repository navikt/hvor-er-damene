import pandas as pd
import json
from datetime import date,datetime

from funksjoner import create_client, get_teamkatalogen_data, write_to_BQ

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'
DATASET = 'teamkatalogen'
def main():

    # Create BigQuery client
    bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

    # Check if this month is already loaded
    this_month = date.today().replace(day=1)
    query = f"SELECT distinct lastet_dato FROM `{PROJECT_ID}.{DATASET}.monthly_snapshot_raw`"
    ld_df = bq_client.query(query).to_dataframe()
    ld_df['lastet_dato'] = pd.to_datetime(ld_df['lastet_dato'], format='%Y-%m-%d').dt.date
    if this_month in ld_df.lastet_dato.values:
        print("month already loaded")
    else:
        print("loading month" + str(this_month)

        # Get data from Teamkatalogen
        df = get_teamkatalogen_data()

        # Process data
        df['lastet_dato'] = date.today()
        df.rename(columns={'Område': 'Omraade'}, inplace=True)

        # Write data to BigQuery
        write_to_BQ(client=bq_client, table_name="monthly_snapshot_raw", dframe=df, dataset=DATASET)

if __name__ == '__main__':
    main()