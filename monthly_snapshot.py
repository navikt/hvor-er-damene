import pandas as pd
import json
from datetime import datetime

from funksjoner import create_client, get_teamkatalogen_data, write_to_BQ

PROJECT_ID = 'heda-prod-2664'
SA_KEY_NAME = 'heda-access-key'
DATASET = 'teamkatalogen'
def main():
    # Get data from Teamkatalogen
    df = get_teamkatalogen_data()

    # Process data
    df['lastet_dato'] = datetime.today()
    df.rename(columns={'Område': 'Omraade'}, inplace=True)

    # Create BigQuery client
    bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

    # Write data to BigQuery
    write_to_BQ(client=bq_client, table_name="monthly_snapshot_raw", dframe=df, dataset=DATASET)

if __name__ == '__main__':
    main()