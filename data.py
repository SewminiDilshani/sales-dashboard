"""Data loading, cleaning and filtering for the Superstore dashboard.

Kept separate from app.py so the logic can be unit-tested without Streamlit.
"""
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "superstore.csv"


def load_raw(path=DATA_PATH):
    """Read the CSV. The file is UTF-8 (latin-1 turns some characters into 'Â')."""
    return pd.read_csv(path, encoding="utf-8", dtype={"Postal Code": "string"})


def clean(df):
    """Parse dates, drop duplicate order lines, fill the missing postal code."""
    df = df.copy()
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d/%m/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d/%m/%Y")

    # Same order line stored twice under different Row IDs
    df = df.drop_duplicates(subset=df.columns.drop("Row ID"))

    # 11 rows, all Burlington, Vermont (ZIP 05401)
    missing = df["Postal Code"].isna() & (df["City"] == "Burlington") & (df["State"] == "Vermont")
    df.loc[missing, "Postal Code"] = "05401"
    return df.reset_index(drop=True)


def load_data(path=DATA_PATH):
    return clean(load_raw(path))


def filter_data(df, regions, categories, segments, start, end):
    mask = (
        df["Region"].isin(regions)
        & df["Category"].isin(categories)
        & df["Segment"].isin(segments)
        & (df["Order Date"] >= pd.to_datetime(start))
        & (df["Order Date"] <= pd.to_datetime(end))
    )
    return df[mask]


def kpis(f):
    """Headline numbers for a (non-empty) filtered frame."""
    total = f["Sales"].sum()
    orders = f["Order ID"].nunique()
    return {
        "total_sales": total,
        "orders": orders,
        "customers": f["Customer ID"].nunique(),
        "avg_order": total / orders,
    }


def yearly_sales(f):
    return f.groupby(f["Order Date"].dt.year)["Sales"].sum().rename_axis("Year").reset_index()


def growth_vs_previous_year(f):
    """(year, % growth) for the last year in f versus the year before, or None."""
    y = yearly_sales(f)
    if len(y) < 2:
        return None
    last, prev = y.iloc[-1], y.iloc[-2]
    return int(last["Year"]), (last["Sales"] / prev["Sales"] - 1) * 100


def peak_month(f):
    """Name of the calendar month with the highest total sales."""
    by_month = f.groupby(f["Order Date"].dt.month)["Sales"].sum()
    return pd.Timestamp(2000, int(by_month.idxmax()), 1).strftime("%B")
