from google.cloud import bigquery

from funksjoner import create_client

SOURCE_PROJECT = "heda-prod-2664"
SOURCE_DATASET = f"{SOURCE_PROJECT}.teamkatalogen"
DESTINATION_PROJECT = "datafolk-prod-94c7"
DESTINATION_DATASET = f"{DESTINATION_PROJECT}.teamkatalogen_01012023_01112026"


def copy_tables(source_client, destination_client):
    source_dataset = source_client.get_dataset(SOURCE_DATASET)
    destination_dataset = bigquery.Dataset(DESTINATION_DATASET)
    destination_dataset.location = source_dataset.location
    destination_dataset = destination_client.create_dataset(
        destination_dataset, exists_ok=True
    )
    if destination_dataset.location != source_dataset.location:
        raise ValueError("Source and destination datasets must have the same location")

    source_tables = list(source_client.list_tables(SOURCE_DATASET))
    existing_tables = {
        table.table_id for table in destination_client.list_tables(DESTINATION_DATASET)
    }
    conflicts = existing_tables.intersection(table.table_id for table in source_tables)
    if conflicts:
        raise ValueError(
            f"Destination tables already exist: {', '.join(sorted(conflicts))}"
        )

    for table in source_tables:
        source_id = f"{SOURCE_DATASET}.{table.table_id}"
        destination_id = f"{DESTINATION_DATASET}.{table.table_id}"
        source_table = source_client.get_table(source_id)
        destination_table = bigquery.Table(destination_id, schema=source_table.schema)
        destination_table.description = source_table.description
        destination_table.labels = source_table.labels
        destination_table.time_partitioning = source_table.time_partitioning
        destination_table.range_partitioning = source_table.range_partitioning
        destination_table.clustering_fields = source_table.clustering_fields

        if (
            source_table.time_partitioning is not None
            and not source_table.time_partitioning.field
        ):
            raise ValueError(
                f"{source_id} uses ingestion-time partitioning, which cannot be "
                "preserved by a pandas transfer; use a BigQuery copy job instead"
            )

        print(f"Reading {source_id}", flush=True)
        dataframe = source_client.query(
            f"SELECT * FROM `{source_id}`",
            location=source_dataset.location,
        ).to_dataframe()

        destination_client.create_table(destination_table)
        if not dataframe.empty:
            job_config = bigquery.LoadJobConfig(
                schema=source_table.schema,
                write_disposition=bigquery.WriteDisposition.WRITE_EMPTY,
            )
            destination_client.load_table_from_dataframe(
                dataframe,
                destination_id,
                job_config=job_config,
                location=destination_dataset.location,
            ).result()
        print(f"Copied {len(dataframe)} rows to {destination_id}", flush=True)


def main():
    source_client = create_client(SOURCE_PROJECT, "heda-access-key")
    destination_client = bigquery.Client(project=DESTINATION_PROJECT)
    copy_tables(source_client, destination_client)


if __name__ == "__main__":
    main()
