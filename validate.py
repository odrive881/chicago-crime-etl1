import pandas as pd
from datetime import datetime
from config import Config
from logger import get_logger, timed_segment

logger = get_logger("validate")


def correct_columns():
    return ["ID", "Case Number", "Date", "Block", "IUCR", "Primary Type", "Description",
               "Location Description", "Arrest", "Domestic", "District", "FBI Code", "X Coordinate",
               "Y Coordinate", "Year", "Latitude", "Longitude"]


def validate_raw(dataframe, column_map):
    """
    Validation layer. Checks for:
    - All columns being present
    - Dates being withing correct range
    - The locations of the crimes actually taking place in Chicago
    - Correct primary types of crimes
    - Makes sure there isn't an anomalous amount of nulls
     """


    columns = column_map

    with timed_segment(logger, "Validation"):

        for col in columns:
            assert col in dataframe.columns, "Not all columns required are present in the dataframe"

        #Date is within 2001 - current year
        acceptable_date_range = {"minimum_date": "2001-01-01", "maximum_date": datetime.today().strftime("%Y-%m-%d")}

        assert dataframe["Date"].min() >= pd.to_datetime(acceptable_date_range["minimum_date"]),\
            f"The dates in the dataset cannot be older than {acceptable_date_range["minimum_date"]}"

        assert dataframe["Date"].max() <= pd.to_datetime(acceptable_date_range["maximum_date"]),\
            f"The dates in the dataset cannot be more recent than {acceptable_date_range["maximum_date"]}"

        #checking for acceptable amount outside bounding box
        long_lower = dataframe.loc[(abs(dataframe["Longitude"]) < 87.5)].shape[0]
        long_upper = dataframe.loc[(abs(dataframe["Longitude"]) > 87.9)].shape[0]
        lat_lower = dataframe.loc[(dataframe["Latitude"] < 41.6)].shape[0]
        lat_upper = dataframe.loc[(dataframe["Latitude"] > 42.1)].shape[0]
        out_of_bounds_sum = lat_upper + lat_lower + long_upper + long_lower
        assert out_of_bounds_sum / dataframe.shape[0] * 100 < 1

        #checking for correct primary types
        accepted_primary_types = ['BATTERY','THEFT','NARCOTICS','ASSAULT','BURGLARY',
                                  'ROBBERY','DECEPTIVE PRACTICE','OTHER OFFENSE',
                                  'CRIMINAL DAMAGE', 'WEAPONS VIOLATION', 'CRIMINAL TRESPASS',
                                  'MOTOR VEHICLE THEFT','SEX OFFENSE', 'INTERFERENCE WITH PUBLIC OFFICER',
                                  'OFFENSE INVOLVING CHILDREN', 'PUBLIC PEACE VIOLATION', 'PROSTITUTION',
                                  'GAMBLING', 'CRIM SEXUAL ASSAULT', 'LIQUOR LAW VIOLATION',
                                  'CRIMINAL SEXUAL ASSAULT', 'ARSON', 'STALKING', 'KIDNAPPING',
                                  'INTIMIDATION', 'CONCEALED CARRY LICENSE VIOLATION', 'NON - CRIMINAL',
                                  'HUMAN TRAFFICKING','OBSCENITY', 'PUBLIC INDECENCY','OTHER NARCOTIC VIOLATION',
                                  'NON-CRIMINAL','HOMICIDE','NON-CRIMINAL (SUBJECT SPECIFIED)',
                                  'RITUALISM', 'DOMESTIC VIOLENCE']

        for p_type in accepted_primary_types:
            assert p_type in dataframe["Primary Type"].values.unique(), "Incorrect Primary Type present in the dataframe"

        #Calculate acceptable null rate per column
        for col in dataframe.columns:
            null_values_percent = (dataframe[col].isnull().sum() / dataframe[col].shape[0])
            assert null_values_percent < Config.max_rejection_rate, f"Too many null values present in {col}"

