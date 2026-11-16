import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import data  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return data.load_data()


def test_duplicate_removed(df):
    assert len(df) == 9799
    assert not df.duplicated(subset=df.columns.drop("Row ID")).any()


def test_no_garbled_characters(df):
    assert not df["Product Name"].str.contains("Â").any()


def test_dates_parsed_and_ordered(df):
    assert pd.api.types.is_datetime64_any_dtype(df["Order Date"])
    assert (df["Ship Date"] >= df["Order Date"]).all()


def test_postal_code_filled(df):
    assert df["Postal Code"].isna().sum() == 0


def test_filter_region_and_dates(df):
    f = data.filter_data(df, ["West"], ["Technology"], df["Segment"].unique(),
                         "2017-01-01", "2017-12-31")
    assert (f["Region"] == "West").all()
    assert f["Order Date"].dt.year.eq(2017).all()


def test_kpis_consistent(df):
    k = data.kpis(df)
    assert k["total_sales"] == pytest.approx(df["Sales"].sum())
    assert k["avg_order"] == pytest.approx(k["total_sales"] / k["orders"])


def test_growth_and_peak_month(df):
    year, pct = data.growth_vs_previous_year(df)
    assert year == 2018 and pct > 0
    assert data.peak_month(df) == "November"
