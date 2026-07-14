import pandas as pd
from logger import get_logger, timed_segment

logger = get_logger("transform")


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


def transform(dataframe):
    """Master function for transforming dataframe"""

    with timed_segment(logger, "Transformation") as details:
        dataframe, log1 = drop_nulls(dataframe)
        dataframe, log2 = deduplicate(dataframe)
        dataframe, log3 = standardize_text(dataframe)
        dataframe, log4 = remove_out_of_bounds(dataframe)

        details["nulls_dropped"] = log1
        details["duplicates_dropped"] = log2
        details["columns_standardized"] = log3
        details["out_of_bounds_dropped"] = log4

    return dataframe
