import pandas as pd
import pytest

from main import CSV_PATH


@pytest.fixture(scope="module")
def df():
    d = pd.read_csv(CSV_PATH, parse_dates=["date"])
    d["yield"] = d.kwh / d.irradiance_kwh_m2
    return d


def test_shape(df):
    assert len(df) == 91 * 4
    assert set(df.array_id) == {"A", "B", "C", "D"}


def test_array_c_loses_yield_after_mid_may(df):
    before = df[df.date < "2025-05-14"].groupby("array_id")["yield"].mean()
    after = df[(df.date >= "2025-05-14") & (df.date != "2025-05-21")].groupby("array_id")["yield"].mean()
    drop = 1 - after / before
    assert drop.idxmax() == "C" and drop["C"] > 0.3
    assert drop.drop("C").max() < 0.15


def test_array_b_fault_burst(df):
    burst = df[(df.array_id == "B") & df.date.between("2025-06-03", "2025-06-06")]
    assert burst.inverter_faults.sum() >= 20
    assert burst.kwh.mean() < 500


def test_curtailment_day_is_zero_everywhere(df):
    day = df[df.date == "2025-05-21"]
    assert (day.kwh == 0).all() and day.irradiance_kwh_m2.iloc[0] > 6
