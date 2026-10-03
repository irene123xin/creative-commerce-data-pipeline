import pandas as pd


def clean_orders(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["order_date"] = pd.to_datetime(result["order_date"], utc=True)
    result["revenue"] = pd.to_numeric(result["revenue"])
    result["discount"] = pd.to_numeric(result["discount"])
    return result

