from config import Config

CRIMES_BY_YEAR_AND_TYPE =   f"""SELECT
                                "Year" AS year,
                                "Primary Type" AS primary_type,
                                ROUND(AVG("Arrest"::int) * 100, 2) AS arrest_percentage,
                                COUNT("Arrest") AS arrest_count
                            FROM {Config.target_schema}.{Config.target_table}
                            GROUP BY 1, 2"""

CRIMES_BY_DISTRICT_MONTH =      f"""SELECT
                                    "Month" AS month,
                                    "District" AS district,
                                    COUNT("Arrest") AS arrest_count
                                FROM {Config.target_schema}.{Config.target_table}
                                GROUP BY 1, 2
                                """

ARREST_RATE_BY_TYPE =      f"""SELECT
                                "Primary Type" AS primary_type,
                                ROUND(AVG("Arrest"::int) * 100, 2) AS arrest_percentage
                            FROM {Config.target_schema}.{Config.target_table}
                            GROUP BY 1
                            ORDER BY AVG("Arrest"::int) DESC"""