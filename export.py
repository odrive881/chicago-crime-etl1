from queries import CRIMES_BY_YEAR_AND_TYPE, CRIMES_BY_DISTRICT_MONTH, ARREST_RATE_BY_TYPE
from sqlalchemy import create_engine, text
from sqlalchemy import inspect
import io
import pandas as pd
from config import Config
from logger import get_logger, timed_segment

logger = get_logger("export")


def get_engine(database_url):
    """Sets up sqlalchemy connection, designed to draw the URL from .env"""
    return create_engine(
        database_url)

def copy_function(dataframe, cursor_conn, raw_sql_conn):
    """
    Transfers the dataframe to SQL. More efficient than to_sql.
    This is the equivalent of using copy in psql manually.
    """
    buffer = io.StringIO()
    dataframe.to_csv(buffer, index=False, header=True, encoding='utf-8')
    buffer.seek(0)
    cursor_conn.copy_expert(f"COPY {Config.target_schema}.{Config.target_table} FROM STDIN WITH (FORMAT csv, HEADER true)", buffer)
    raw_sql_conn.commit()

def load_to_sql(dataframe, engine_function, database_url):
    """
    Orchestrates the transfer of the DF to Postgres.
    Raises error if identical DF has already been transferred.
    """

    skip_load = False
    engine = engine_function(database_url)
    inspector = inspect(engine)
    exists = inspector.has_table(Config.target_table, schema=Config.target_schema)
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    with timed_segment(logger, "Export") as details:
        try:

            with engine.begin() as conn:
                if exists:
                    sql_row_num = pd.read_sql(text(f"SELECT COUNT(*) FROM {Config.target_schema}.{Config.target_table}"), conn)
                    sql_col_num = pd.read_sql(text(f"SELECT COUNT(*) FROM "
                                                   f"information_schema.columns "
                                                   f"WHERE table_schema = '{Config.target_schema}' "
                                                   f"AND table_name = '{Config.target_table}'"), conn)

            if exists and sql_row_num.iloc[0, 0] == len(dataframe) and sql_col_num.iloc[0, 0] == len(dataframe.columns) and not skip_load:
                logger.warning("The Dataframe already exists in SQL, export stopped")
                details["result"] = "skipped, dataframe already exists"
                skip_load = True

            elif exists and sql_row_num.iloc[0, 0] != len(dataframe) and sql_col_num.iloc[0, 0] != len(dataframe.columns) and not skip_load:
                copy_function(dataframe, cursor, raw_conn)
                logger.info("Dataframe successfully exported to SQL")
                details["result"] = "exported"

            if not exists and not skip_load:
                dataframe.head(0).to_sql(name=Config.target_table, schema=Config.target_schema, con=engine, if_exists='replace', index=False)
                copy_function(dataframe, cursor, raw_conn)
                logger.info("Dataframe successfully exported to SQL")
                details["result"] = "exported"

        finally:
            raw_conn.close()
            engine.dispose()

def create_summaries(engine, db_url):
    with timed_segment(logger, "Summary tables export") as details:
        inspector = inspect(engine(db_url))

        exists1 = inspector.has_table("crimes_by_year" ,schema=Config.target_schema)
        exists2 = inspector.has_table("crimes_by_district", schema=Config.target_schema)
        exists3 = inspector.has_table("arrest_rate", schema=Config.target_schema)

        if not exists1 and not exists2 and not exists3:
            with engine(db_url).begin() as conn:
                conn.execute(text(f"""CREATE TABLE IF NOT EXISTS crimes_by_year AS {CRIMES_BY_YEAR_AND_TYPE}"""))
                conn.execute(text(f"""CREATE TABLE IF NOT EXISTS crimes_by_district AS {CRIMES_BY_DISTRICT_MONTH}"""))
                conn.execute(text(f"""CREATE TABLE IF NOT EXISTS arrest_rate AS {ARREST_RATE_BY_TYPE}"""))
                logger.info("Summary tables created in Postgres")
                details["result"] = "created"

        if exists1 and exists2 and exists3:
            logger.warning("Summary tables already exist, skipping load")
            details["result"] = "skipped, summary tables already exist"

        engine(db_url).dispose()
