from google.cloud import bigquery
import pathlib


PROJECT = "heda-prod-2664"
#
SQL_DIR = pathlib.Path(__file__).parent


def load_sql(filepath: pathlib.Path):
    query = filepath.read_text()
    return query


def get_client(project: str):
    return bigquery.Client(project=project)


def split_roller(roller: str) -> list[str]:
    pass


def main():
    client = get_client(PROJECT)
    query = load_sql(SQL_DIR / "team_gender.sql")
    df = client.query(query).to_dataframe()

    df.query("Roller == 'Utvikler'").pivot_table(
        index="Team", columns="gender_pred", aggfunc="size"
    ).fillna(0).female.value_counts()

    df = df.pivot_table(index="Team", columns="gender_pred", aggfunc="size").fillna(0)

    df.female.value_counts()

    df.groupby(["Team", "gender_pred"], as_index=False).size()


if __name__ == "__main__":
    main()
