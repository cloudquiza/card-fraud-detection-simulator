"""
generate_synthetic_card_data.py

This script generates synthetic card transaction data to simulate
card-present and card-not-present (CNP) behavior, including some
fraud patterns.

Output:
- data/card_transactions.csv

Each row represents a single card transaction.
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_card_profiles(num_cards: int = 1000) -> pd.DataFrame:
    """
    Create a set of synthetic card profiles.

    Each card has:
    - card_id: internal identifier
    - bin: first 6 digits of card number (represents issuer / product)
    - brand: Visa, Mastercard, etc.
    - card_type: credit, debit, prepaid
    - home_country: where the cardholder is based (for geo mismatch logic)
    """

    bins = [
        ("400000", "Visa", "credit"),
        ("400100", "Visa", "debit"),
        ("510000", "Mastercard", "credit"),
        ("520000", "Mastercard", "debit"),
        ("530000", "Mastercard", "prepaid"),  # use this as higher risk
        ("370000", "Amex", "credit"),
    ]

    countries = ["US", "CA", "GB", "FR", "DE", "AU", "BR", "MX"]

    cards = []
    for i in range(num_cards):
        bin_value, brand, base_type = random.choice(bins)

        # Slightly bias prepaid to be less common overall
        if base_type == "prepaid":
            # reduce frequency by skipping some iterations for prepaid
            if random.random() < 0.5:
                bin_value, brand, base_type = random.choice(
                    [b for b in bins if b[2] != "prepaid"]
                )

        home_country = random.choice(countries)

        card = {
            "card_id": f"card_{i+1}",
            "bin": bin_value,
            "brand": brand,
            "card_type": base_type,
            "home_country": home_country,
        }
        cards.append(card)

    return pd.DataFrame(cards)


def random_ip_for_country(country: str) -> str:
    """
    Generate a simple synthetic IP-like string.

    This does not map to real geolocation, but we can use the
    first octet to loosely represent region.

    Example:
    - US, CA: 23.x.x.x
    - EU countries: 51.x.x.x
    - Others: 101.x.x.x
    """

    if country in ["US", "CA"]:
        first_octet = 23
    elif country in ["GB", "FR", "DE"]:
        first_octet = 51
    else:
        first_octet = 101

    return f"{first_octet}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"


def generate_merchants(num_merchants: int = 200) -> pd.DataFrame:
    """
    Create synthetic merchants with MCC codes and countries.

    We include some higher risk MCCs such as:
    - 5968: Direct marketing
    - 4816: Computer network services
    - 7995: Betting (high risk)
    - 6051: Quasi cash (often high risk)
    """

    mccs = [
        "5411",  # Grocery stores
        "5732",  # Electronics stores
        "4814",  # Telecom services
        "4816",  # Computer network / info services (higher risk)
        "5968",  # Direct marketing (higher risk)
        "5999",  # Misc retail
        "6011",  # ATM / Financial institutions
        "6051",  # Quasi cash (higher risk)
        "7995",  # Betting (higher risk)
    ]

    countries = ["US", "CA", "GB", "FR", "DE", "AU", "BR", "MX"]

    merchants = []
    for i in range(num_merchants):
        merchant_id = f"m_{i+1}"
        mcc = random.choice(mccs)
        country = random.choice(countries)

        merchants.append(
            {
                "merchant_id": merchant_id,
                "mcc": mcc,
                "merchant_country": country,
            }
        )

    return pd.DataFrame(merchants)


def generate_transactions(
    cards: pd.DataFrame,
    merchants: pd.DataFrame,
    num_transactions: int = 10000,
) -> pd.DataFrame:
    """
    Generate synthetic card transactions.

    For each transaction we choose:
    - a card
    - a merchant
    - card_present flag
    - amount
    - timestamp
    - device_id
    - ip_country (may match or mismatch home_country)
    - ip_address (derived from ip_country)
    - baseline auth_result (approved / declined)
    - is_fraud_pattern (label used later for evaluation)
    - chargeback (some fraud patterns produce chargebacks)
    """

    # Time range: last 60 days
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=60)

    records = []

    # For some fraud patterns, we will pre-select subsets of cards
    num_cards = len(cards)
    fraud_card_testing_cards = cards.sample(
        n=max(5, num_cards // 50), random_state=42
    )  # many small CNP authorizations
    fraud_high_risk_bin_cards = cards[cards["card_type"] == "prepaid"]
    fraud_geo_mismatch_cards = cards.sample(
        n=max(10, num_cards // 25), random_state=99
    )

    for i in range(num_transactions):
        tx_id = f"tx_{i+1}"

        # Pick a card and merchant
        card = cards.sample(n=1).iloc[0]
        merchant = merchants.sample(n=1).iloc[0]

        # Card present vs not present
        # CNP is more common for certain MCCs like digital goods or network services
        mcc = merchant["mcc"]
        if mcc in ["4816", "5968", "7995", "6051"]:
            card_present = False
        else:
            card_present = random.random() < 0.4  # 40 percent card present, 60 percent CNP

        # Base amount distribution
        if mcc in ["5411"]:
            # Grocery
            amount = round(np.random.gamma(shape=2.0, scale=30.0), 2)
        elif mcc in ["5732"]:
            # Electronics
            amount = round(np.random.uniform(50, 800), 2)
        elif mcc in ["7995", "6051"]:
            # Betting / quasi cash
            amount = round(np.random.uniform(20, 1000), 2)
        else:
            amount = round(np.random.uniform(5, 300), 2)

        # Timestamp uniform over last 60 days
        delta = end_time - start_time
        random_seconds = random.randint(0, int(delta.total_seconds()))
        timestamp = start_time + timedelta(seconds=random_seconds)

        # Default IP country is home_country (no mismatch)
        ip_country = card["home_country"]

        # Device
        device_id = f"device_{random.randint(1, 5000)}"

        # Baseline labels
        is_fraud_pattern = False
        chargeback = 0
        fraud_scenario = None

        # -----------------------------
        # Fraud pattern 1: card testing
        # -----------------------------
        # Many small CNP purchases in short periods on a subset of cards.
        if card["card_id"] in set(fraud_card_testing_cards["card_id"]):
            if not card_present and amount < 10:
                # Increase chance this is a fraud test
                if random.random() < 0.4:
                    is_fraud_pattern = True
                    fraud_scenario = "card_testing"
                    # Higher chance of decline or chargeback later
                    chargeback = 1 if random.random() < 0.3 else 0

        # ---------------------------------------------
        # Fraud pattern 2: high-risk BIN prepaids usage
        # ---------------------------------------------
        if not is_fraud_pattern and card["card_type"] == "prepaid":
            if mcc in ["7995", "6051", "5968"]:
                if random.random() < 0.25:
                    is_fraud_pattern = True
                    fraud_scenario = "high_risk_bin_mcc"
                    chargeback = 1 if random.random() < 0.25 else 0

        # --------------------------------------------------
        # Fraud pattern 3: geo mismatch with high-risk MCCs
        # --------------------------------------------------
        if not is_fraud_pattern and card["card_id"] in set(
            fraud_geo_mismatch_cards["card_id"]
        ):
            # Make IP originate from another region
            possible_countries = ["US", "CA", "GB", "FR", "DE", "AU", "BR", "MX"]
            other_countries = [c for c in possible_countries if c != card["home_country"]]
            ip_country = random.choice(other_countries)

            if not card_present and mcc in ["4816", "5968", "7995", "6051"]:
                if random.random() < 0.3:
                    is_fraud_pattern = True
                    fraud_scenario = "geo_mismatch_cnp_high_risk_mcc"
                    chargeback = 1 if random.random() < 0.35 else 0

        # ------------------------------
        # Fraud pattern 4: amount spikes
        # ------------------------------
        if not is_fraud_pattern:
            # Randomly mark some very high transactions as suspicious
            if amount > 700 and not card_present and random.random() < 0.2:
                is_fraud_pattern = True
                fraud_scenario = "high_amount_cnp"
                chargeback = 1 if random.random() < 0.3 else 0

        # Authorization result
        # Very simple logic:
        # - Fraud patterns have higher chance to be declined
        # - Otherwise most transactions are approved
        if is_fraud_pattern:
            auth_result = "declined" if random.random() < 0.5 else "approved"
        else:
            auth_result = "approved" if random.random() < 0.95 else "declined"

        # Build IP address string from ip_country
        ip_address = random_ip_for_country(ip_country)

        record = {
            "transaction_id": tx_id,
            "card_id": card["card_id"],
            "bin": card["bin"],
            "brand": card["brand"],
            "card_type": card["card_type"],
            "home_country": card["home_country"],
            "merchant_id": merchant["merchant_id"],
            "mcc": merchant["mcc"],
            "merchant_country": merchant["merchant_country"],
            "amount": amount,
            "currency": "USD",  # keep simple
            "card_present": card_present,
            "timestamp": timestamp.isoformat(),
            "device_id": device_id,
            "ip_country": ip_country,
            "ip_address": ip_address,
            "auth_result": auth_result,
            "is_fraud_pattern": int(is_fraud_pattern),
            "fraud_scenario": fraud_scenario,
            "chargeback": chargeback,
        }

        records.append(record)

    return pd.DataFrame(records)


def main():
    # Set seeds so results are reproducible
    random.seed(42)
    np.random.seed(42)

    print("Generating card profiles...")
    cards = generate_card_profiles(num_cards=1200)

    print("Generating merchants...")
    merchants = generate_merchants(num_merchants=250)

    print("Generating transactions...")
    transactions = generate_transactions(cards, merchants, num_transactions=15000)

    # Ensure data folder exists and save
    output_path = "data/card_transactions.csv"
    transactions.to_csv(output_path, index=False)

    print(f"Saved {len(transactions)} transactions to {output_path}")


if __name__ == "__main__":
    main()
