import pandas as pd
import json
from datetime import datetime

def drop_nulls(dataframe):
    """Drops nulls in dataframe"""
    total_null = dataframe.isnull().sum().sum()
    dataframe = dataframe.dropna()
    rows_check_nulls = f"total nulls dropped: {total_null}"
    print(rows_check_nulls)
    return dataframe, str(total_null)

def deduplicate(dataframe):
    """Removes duplicates in dataframe"""
    total_duplicates = dataframe.duplicated().sum()
    dataframe = dataframe.drop_duplicates()
    rows_check_duplicates = f"total duplicates dropped: {total_duplicates}"
    print(rows_check_duplicates)
    return dataframe, str(total_duplicates)

def standardize_text(dataframe):
    """Strips whitespace and applies title case to column names"""
    for column in dataframe.columns:
        cleaned_col_name = column.strip().title()
        dataframe = dataframe.rename(columns={column: cleaned_col_name})
    column_name_list = [column for column in dataframe.columns]
    return dataframe, str(len(column_name_list))

def remove_out_of_bounds(dataframe):
    """Removes rows which have taken place outside the bounding box for Chicago: ~41.6-42.1 N and ~87.5-87.9 W"""
    rows_before = dataframe.shape[0]
    dataframe = dataframe.loc[(dataframe["Latitude"] >= 41.6) & (dataframe["Latitude"] <= 42.1) & (abs(dataframe["Longitude"]) >= 87.5) & (abs(dataframe["Longitude"]) <= 87.9)]
    rows_after = dataframe.shape[0]
    rows_out_of_bounds = f"out of bounds cases dropped: {rows_before - rows_after}"
    print(rows_out_of_bounds)
    return dataframe, str(rows_before - rows_after)


def classify_severity(dataframe):
    """Classifies the types of crimes that have taken place"""
    violent_crimes = ["HOMICIDE", "ASSAULT", "BATTERY", "ROBBERY", "ARSON", "CRIMINAL SEXUAL ASSAULT"]
    property_crimes = ["THEFT", "BURGLARY", "MOTOR VEHICLE THEFT", "CRIMINAL DAMAGE", "CRIMINAL TRESPASS"]
    return dataframe["Primary Type"].map(lambda x: "violent" if x in violent_crimes
                                            else "property" if x in property_crimes
                                            else "other")


def export_log(nulls_check, duplicate_check, columns_text_check, out_of_bounds_check):
    """Exports log to json file"""
    log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = {"Transformation": "Complete",
           "time": log_date,
           "nulls dropped": nulls_check,
           "duplicate dropped": duplicate_check,
           "columns standardized": columns_text_check,
           "out of bounds": out_of_bounds_check}
    with open("chicago_data/pipeline_log.json", "a") as file:
        json.dump(log, file, indent=2)


def transform(dataframe):
    """Master function for transforming dataframe"""
    print("Transforming dataframe...")
    dataframe, log1 = drop_nulls(dataframe)
    dataframe, log2 = deduplicate(dataframe)
    dataframe, log3 = standardize_text(dataframe)
    dataframe, log4 = remove_out_of_bounds(dataframe)

    export_log(
        log1, log2, log3, log4
    )

    print("Transformation complete!")
    return dataframe


