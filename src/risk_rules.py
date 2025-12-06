"""
risk_rules.py

This module contains rule based logic for card fraud detection.

Input:
    A pandas DataFrame with card transaction data. It should already include
    some enriched fields that make rules easier to compute, such as:
        - device_unique_cards
        - small_cnp_tx_count

Output:
    - scored_df: original dataframe with added columns:
        * risk_score (numeric)
        * triggered_rules (string with comma separated rule names)
    - alerts_df: long format table where each row is a rule hit on a transaction.
"""

from typing import Callable, Dict, List, Tuple

import pandas as pd


# Type alias for a rule condition function
RuleCondition = Callable[[pd.DataFrame], pd.Series]


def get_rules() -> List[Dict]:
    """
    Define the rules used for card fraud detection.

    Each rule is a dictionary with:
        - name: short identifier
        - description: human readable description
        - weight: numeric weight added to risk_score when the rule fires
        - condition: a function that takes the DataFrame and returns a boolean Series
    """

    high_risk_mccs = ["7995", "6051", "5968", "4816"]

    rules: List[Dict] = [
        {
            "name": "high_amount_cnp",
            "description": "High amount card not present transaction",
            "weight": 25,
            "condition": lambda df: (~df["card_present"]) & (df["amount"] >= 500),
        },
        {
            "name": "high_risk_mcc",
            "description": "High risk MCC with moderate or high amount",
            "weight": 20,
            "condition": lambda df: (
                df["mcc"].isin(high_risk_mccs) & (df["amount"] >= 100)
            ),
        },
        {
            "name": "prepaid_high_risk_mcc",
            "description": "Prepaid card used at high risk merchant category",
            "weight": 20,
            "condition": lambda df: (
                (df["card_type"] == "prepaid") & df["mcc"].isin(high_risk_mccs)
            ),
        },
        {
            "name": "geo_mismatch_cnp",
            "description": "Card not present and IP country different from home country",
            "weight": 20,
            "condition": lambda df: (
                (~df["card_present"]) & (df["ip_country"] != df["home_country"])
            ),
        },
        {
            "name": "shared_device_many_cards",
            "description": "Device used by many different cards",
            "weight": 15,
            "condition": lambda df: df["device_unique_cards"] >= 5,
        },
        {
            "name": "card_testing_pattern",
            "description": "Card has many small card not present transactions",
            "weight": 20,
            "condition": lambda df: df["small_cnp_tx_count"] >= 10,
        },
        {
            "name": "declined_high_amount",
            "description": "High amount transaction that was declined",
            "weight": 10,
            "condition": lambda df: (df["amount"] >= 400) & (df["auth_result"] == "declined"),
        },
    ]

    return rules


def apply_rules(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply all rules to the transactions DataFrame.

    Returns:
        scored_df: original dataframe with risk_score and triggered_rules columns
        alerts_df: long format table of individual rule hits per transaction
    """

    rules = get_rules()

    # Work on a copy so we do not modify the original input accidentally
    scored_df = df.copy()

    # Initialize risk score and triggered rules columns
    scored_df["risk_score"] = 0
    scored_df["triggered_rules"] = ""

    alerts_rows = []

    for rule in rules:
        name = rule["name"]
        description = rule["description"]
        weight = rule["weight"]
        condition = rule["condition"]

        # condition(df) returns a boolean Series with True where the rule fires
        mask = condition(scored_df)

        # Update risk score where the rule fires
        scored_df.loc[mask, "risk_score"] += weight

        # Append rule name to triggered_rules for those rows
        # If triggered_rules is empty, just set the name. Otherwise append with comma.
        current_values = scored_df.loc[mask, "triggered_rules"].astype(str)
        updated_values = current_values.where(
            current_values == "",
            current_values + "," + name,
        )
        updated_values = updated_values.where(current_values != "", name)

        scored_df.loc[mask, "triggered_rules"] = updated_values

        # Build alert rows for this rule
        hits = scored_df.loc[mask, [
            "transaction_id",
            "card_id",
            "bin",
            "mcc",
            "amount",
            "card_present",
            "device_id",
            "ip_country",
            "home_country",
        ]].copy()

        hits["rule_name"] = name
        hits["rule_description"] = description
        hits["rule_weight"] = weight

        alerts_rows.append(hits)

    # Combine all alerts into a single DataFrame
    if alerts_rows:
        alerts_df = pd.concat(alerts_rows, ignore_index=True)
    else:
        alerts_df = pd.DataFrame(
            columns=[
                "transaction_id",
                "card_id",
                "bin",
                "mcc",
                "amount",
                "card_present",
                "device_id",
                "ip_country",
                "home_country",
                "rule_name",
                "rule_description",
                "rule_weight",
            ]
        )

    return scored_df, alerts_df
