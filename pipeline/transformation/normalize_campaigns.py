import pandas as pd


def normalize_campaigns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["channel"] = result["channel"].str.lower().str.strip()
    result["start_date"] = pd.to_datetime(result["start_date"]).dt.date
    result["end_date"] = pd.to_datetime(result["end_date"]).dt.date
    return result

