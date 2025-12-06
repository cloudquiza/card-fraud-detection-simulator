"""
run_scoring.py

This script loads synthetic card transactions, enriches them with
helper fields, applies rule based fraud detection, and writes out:

- data/card_transactions_scored.csv
- data/card_alerts.csv
"""

import os

import pandas as pd

from risk_rules import apply_rules


def enrich_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add helper fields that make rules easier to compute.

    Adds:
        - device_unique_cards: how many unique cards have used this device
        - small_cnp_tx_count: how many small card not present transactions each card has
    """

    enriched = df.copy()

    # Convert timestamp to datetime for any future time based work
    enriched["timestamp"] = pd.to_datetime(enriched["timestamp"])

    # 1. device_unique_cards: number of distinct cards per device
    device_counts = (
        enriched.groupby("device_id")["card_id"]
        .nunique()
        .reset_index(name="device_unique_cards")
    )

    enriched = enriched.merge(device_counts, on="device_id", how="left")

    # 2. small_cnp_tx_count: for each card, how many small CNP transactions it has
    small_cnp_mask = (~enriched["card_present"]) & (enriched["amount"] < 10)

    small_cnp_counts = (
        enriched[small_cnp_mask]
        .groupby("card_id")["transaction_id"]
        .count()
        .reset_index(name="small_cnp_tx_count")
    )

    enriched = enriched.merge(small_cnp_counts, on="card_id", how="left")

    # For cards without any small CNP transactions, fill nulls with zero
    enriched["small_cnp_tx_count"] = enriched["small_cnp_tx_count"].fillna(0).astype(int)

    return enriched


def main():
    input_path = "data/card_transactions.csv"
    scored_output_path = "data/card_transactions_scored.csv"
    alerts_output_path = "data/card_alerts.csv"

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found at {input_path}. "
            f"Run generate_synthetic_card_data.py first."
        )

    print(f"Loading transactions from {input_path}...")
    df = pd.read_csv(input_path)

    print("Enriching transactions with helper fields...")
    enriched_df = enrich_transactions(df)

    print("Applying risk rules...")
    scored_df, alerts_df = apply_rules(enriched_df)

    # Save outputs
    print(f"Writing scored transactions to {scored_output_path}...")
    scored_df.to_csv(scored_output_path, index=False)

    print(f"Writing alerts to {alerts_output_path}...")
    alerts_df.to_csv(alerts_output_path, index=False)

    # Simple summary for the console
    high_risk = scored_df[scored_df["risk_score"] >= 40]
    print()
    print("Summary:")
    print(f"Total transactions: {len(scored_df)}")
    print(f"Total alerts: {len(alerts_df)}")
    print(f"High risk transactions (risk_score >= 40): {len(high_risk)}")


if __name__ == "__main__":
    main()
