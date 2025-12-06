"""
streamlit_app.py

Card Fraud Detection Simulator dashboard.

This app:
- Loads scored card transactions and rule alerts
- Lets you filter by risk, MCC, brand, card type, and card-present vs CNP
- Shows KPIs, charts, and tables for high risk behavior
"""

import pathlib

import pandas as pd
import streamlit as st


# ---------- Helpers ----------

@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load scored transactions and alerts from the data folder.

    Uses a relative path so the app works no matter where it is launched from.
    """

    base_dir = pathlib.Path(__file__).resolve().parents[1]
    tx_path = base_dir / "data" / "card_transactions_scored.csv"
    alerts_path = base_dir / "data" / "card_alerts.csv"

    df = pd.read_csv(tx_path)
    alerts = pd.read_csv(alerts_path)

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Create a risk bucket for easier grouping
    df["risk_bucket"] = pd.cut(
        df["risk_score"],
        bins=[-1, 0, 20, 40, 100],
        labels=["0", "1-20", "21-40", "41+"]
    )

    # Ensure some columns are in expected types
    df["is_fraud_pattern"] = df["is_fraud_pattern"].astype(int)
    df["chargeback"] = df["chargeback"].astype(int)

    return df, alerts


def format_rate(x: float) -> str:
    """Format a float as a percentage string."""
    return f"{x * 100:.1f}%"


# ---------- Main app ----------

def main():
    st.set_page_config(
        page_title="Card Fraud Detection Simulator",
        layout="wide",
    )

    st.title("Card Fraud Detection Simulator")
    st.caption(
        "Synthetic card transaction data with rule based fraud scoring, "
        "built to practice how card risk systems behave."
    )

    # Load data
    df, alerts = load_data()

    # ---------- Sidebar filters ----------

    st.sidebar.header("Filters")

    # Risk score slider
    min_risk, max_risk = int(df["risk_score"].min()), int(df["risk_score"].max())
    risk_range = st.sidebar.slider(
        "Risk score range",
        min_value=min_risk,
        max_value=max_risk,
        value=(min_risk, max_risk),
        step=1,
    )

    # Card present vs CNP
    card_present_filter = st.sidebar.selectbox(
        "Card present vs CNP",
        options=["All", "Card present only", "Card not present only"],
    )

    # Brand filter
    brands = sorted(df["brand"].dropna().unique().tolist())
    selected_brands = st.sidebar.multiselect(
        "Card brands",
        options=brands,
        default=brands,
    )

    # Card type filter
    card_types = sorted(df["card_type"].dropna().unique().tolist())
    selected_card_types = st.sidebar.multiselect(
        "Card types",
        options=card_types,
        default=card_types,
    )

    # MCC filter
    mcc_values = sorted(df["mcc"].dropna().unique().tolist())
    selected_mccs = st.sidebar.multiselect(
        "MCCs",
        options=mcc_values,
        default=mcc_values,
    )

    high_risk_only = st.sidebar.checkbox(
        "Show high risk transactions only (risk_score >= 40)",
        value=False,
    )

    # ---------- Apply filters ----------

    filtered = df.copy()

    # Risk score range filter
    filtered = filtered[
        (filtered["risk_score"] >= risk_range[0])
        & (filtered["risk_score"] <= risk_range[1])
    ]

    # Card present vs CNP filter
    if card_present_filter == "Card present only":
        filtered = filtered[filtered["card_present"] == True]
    elif card_present_filter == "Card not present only":
        filtered = filtered[filtered["card_present"] == False]

    # Brand filter
    filtered = filtered[filtered["brand"].isin(selected_brands)]

    # Card type filter
    filtered = filtered[filtered["card_type"].isin(selected_card_types)]

    # MCC filter
    filtered = filtered[filtered["mcc"].isin(selected_mccs)]

    # High risk filter
    if high_risk_only:
        filtered = filtered[filtered["risk_score"] >= 40]

    # Guard against empty result
    if filtered.empty:
        st.warning("No transactions match the current filters.")
        return

    # ---------- Top KPIs ----------

    total_tx = len(filtered)
    approval_rate = (filtered["auth_result"] == "approved").mean()
    fraud_rate = filtered["is_fraud_pattern"].mean()
    chargeback_rate = filtered["chargeback"].mean()
    high_risk_count = (filtered["risk_score"] >= 40).sum()
    high_risk_rate = high_risk_count / total_tx

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Transactions", f"{total_tx:,}")
    col2.metric("Approval rate", format_rate(approval_rate))
    col3.metric("Fraud pattern rate", format_rate(fraud_rate))
    col4.metric("Chargeback rate", format_rate(chargeback_rate))
    col5.metric("High risk rate", format_rate(high_risk_rate))

    st.markdown("---")

    # ---------- Charts row ----------

    st.subheader("Risk distribution and patterns")

    col_left, col_right = st.columns(2)

    # Risk score histogram
    with col_left:
        st.markdown("**Risk score distribution**")

        # Robust version that always has risk_score + count
        risk_hist = (
            filtered.groupby("risk_score", observed=False)
            .size()
            .reset_index(name="count")
            .sort_values("risk_score")
        )

        st.bar_chart(
            risk_hist.set_index("risk_score")["count"],
            height=300,
        )

    # MCC average risk
    with col_right:
        st.markdown("**Top MCCs by average risk score**")
        mcc_summary = (
            filtered.groupby("mcc", observed=False)
            .agg(
                avg_risk=("risk_score", "mean"),
                tx_count=("transaction_id", "count"),
            )
            .sort_values("avg_risk", ascending=False)
            .head(10)
        )
        st.bar_chart(
            mcc_summary["avg_risk"],
            height=300,
        )

    st.markdown("---")

    # ---------- BIN and bucket insights ----------

    st.subheader("BIN and risk bucket insights")

    col_bin, col_bucket = st.columns(2)

    with col_bin:
        st.markdown("**Top BINs by average risk score**")
        bin_summary = (
            filtered.groupby("bin", observed=False)
            .agg(
                avg_risk=("risk_score", "mean"),
                tx_count=("transaction_id", "count"),
            )
            .sort_values("avg_risk", ascending=False)
            .head(10)
        )
        st.dataframe(bin_summary)

    with col_bucket:
        st.markdown("**Risk buckets (0, 1-20, 21-40, 41+)**")
        bucket_counts = (
            filtered["risk_bucket"]
            .value_counts()
            .sort_index()
            .rename_axis("risk_bucket")
            .to_frame("count")
        )
        st.bar_chart(bucket_counts, height=300)

    st.markdown("---")

    # ---------- High risk entities ----------

    st.subheader("High risk cards and devices")

    high_risk = filtered[filtered["risk_score"] >= 40]

    if not high_risk.empty:
        card_group = (
            high_risk.groupby("card_id", observed=False)
            .agg(
                max_risk=("risk_score", "max"),
                tx_count=("transaction_id", "count"),
                avg_amount=("amount", "mean"),
                fraud_hits=("is_fraud_pattern", "sum"),
                chargebacks=("chargeback", "sum"),
            )
            .sort_values(["max_risk", "tx_count"], ascending=False)
            .head(25)
        )

        st.markdown("**Top high risk cards**")
        st.dataframe(card_group)

        device_group = (
            high_risk.groupby("device_id", observed=False)
            .agg(
                unique_cards=("card_id", "nunique"),
                tx_count=("transaction_id", "count"),
                avg_risk=("risk_score", "mean"),
            )
            .sort_values(["unique_cards", "avg_risk"], ascending=False)
            .head(25)
        )

        st.markdown("**Devices associated with many high risk cards**")
        st.dataframe(device_group)
    else:
        st.info("No high risk transactions in the current filter selection.")

    st.markdown("---")

    # ---------- Rule level view ----------

    st.subheader("Rule alerts")

    if not alerts.empty:
        # Join alerts with filtered view so we only show relevant ones
        filtered_ids = filtered["transaction_id"].unique().tolist()
        alerts_filtered = alerts[alerts["transaction_id"].isin(filtered_ids)]

        rule_counts = (
            alerts_filtered["rule_name"]
            .value_counts()
            .rename_axis("rule_name")
            .to_frame("count")
        )

        st.markdown("**Alert counts by rule**")
        st.dataframe(rule_counts)

        with st.expander("Sample alerts"):
            st.dataframe(alerts_filtered.head(100))
    else:
        st.info("No alerts available.")

    st.markdown("---")

    st.caption(
        "This dashboard is built on fully synthetic data. "
        "The focus is on how I think about card risk patterns, "
        "not on any specific production data."
    )


if __name__ == "__main__":
    main()
