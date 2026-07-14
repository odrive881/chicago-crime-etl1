import pandas as pd
from sqlalchemy import text

from validate import validate_raw
from validate import correct_columns

from transform import classify_severity
from transform import transform

from export import get_engine
from export import load_to_sql
from export import create_summaries

from config import Config


"""Main ingestion logic"""
dtype_map = {
    "ID": "uint32",
    "Case Number": "string",
    "Block": "string",
    "IUCR": "string",
    "Primary Type": "category",
    "Description": "category",
    "Location Description": "category",
    "Arrest": "bool",
    "Domestic": "bool",
    "Beat": "uint16",
    "District": "UInt8",
    "Ward": "UInt8",
    "Community Area": "UInt8",
    "FBI Code": "category",
    "X Coordinate": "UInt32",
    "Y Coordinate": "UInt32",
    "Year": "uint16",
    "Updated On": "string",
    "Latitude": "float32",
    "Longitude": "float32",
    "Location": "string"
}

columns = correct_columns()
df = pd.read_csv(Config.raw_file_path, usecols=columns,  dtype=dtype_map, parse_dates=['Date'], date_format='%m/%d/%Y %H:%M:%S %p')


df["Month"] = df["Date"].dt.month.astype('uint16')
df["Day"] = df["Date"].dt.day_name().astype('category')
df["Hour"] = df["Date"].dt.hour.astype('uint16')

memory_usage = df.memory_usage(deep=True).sum()

"""Validation, Transformation, Export to SQL"""
validate_raw(df, columns)
df = transform(df)
df["Severity"] = classify_severity(df)
load_to_sql(df, get_engine, Config.db_url)


"""Summary marts creation"""
create_summaries(get_engine, Config.db_url)
