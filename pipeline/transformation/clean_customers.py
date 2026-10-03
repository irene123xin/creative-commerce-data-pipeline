import pandas as pd


def clean_customers(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["signup_date"] = pd.to_datetime(result["signup_date"]).dt.date
    result["acquisition_channel"] = result["acquisition_channel"].str.lower().str.strip()
    return result

