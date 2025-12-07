"""
export_for_bi.py

Prepare scored card fraud data for BI tools (Tableau, Power BI, etc.).

This script:
- Loads data/card_transactions_scored.csv
- Adds a simple risk bucket based on risk_score if needed
- Keeps the most useful analytics fields
- Writes a clean CSV to data/card_transactions_for_bi.csv
"""

import pandas as pd


def main():
    input_path = "data/card_transactions_scored.csv"
    output_path = "data/card_transactions_for_bi.csv"

    df = pd.read_csv(input_path)

    # If risk_bucket is not present, create it based on risk_score
    if "risk_bucket" not in df.columns:
        df["risk_bucket"] = pd.cut(
            df["risk_score"],
            bins=[-1, 0, 20, 40, 100],
            labels=["0", "1-20", "21-40", "41+"]
        )

    # Select columns that are useful in BI / dashboards
    bi_df = df[
        [
            "transaction_id",
            "card_id",
            "bin",
            "brand",
            "card_type",
            "home_country",
            "merchant_id",
            "mcc",
            "merchant_country",
            "amount",
            "currency",
            "card_present",
            "timestamp",
            "device_id",
            "ip_country",
            "auth_result",
            "risk_score",
            "risk_bucket",
            "is_fraud_pattern",
            "chargeback",
        ]
    ].copy()

    bi_df.to_csv(output_path, index=False)
    print(f"Wrote BI-ready file to {output_path} with {len(bi_df)} rows.")


if __name__ == "__main__":
    main()
