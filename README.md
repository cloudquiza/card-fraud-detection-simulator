# Card Fraud Detection Simulator

Synthetic card transaction data, fraud patterns, rule based scoring, and an interactive dashboard.
Built to practice how modern card fraud and payments risk systems behave in a fintech or issuer/acquirer environment.

![Dashboard Screenshot](docs/img/card_dashboard_1.png)
![Dashboard Screenshot](docs/img/card_dashboard_2.png)
![Dashboard Screenshot](docs/img/card_dashboard_3.png)
![Dashboard Screenshot](docs/img/card_dashboard_4.png)

<p align="center">
  <em>Interactive Streamlit dashboard showing risk scores, MCC/BIN insights, and high-risk entities.</em>
</p>

---

## At a glance

**What this project demonstrates:**

- Ability to think like a payments risk analyst working in card fraud.
- Understanding of card-not-present (CNP) fraud, MCC patterns, BIN behavior, and device/IP risk.
- Python and pandas for synthetic data generation and fraud pattern simulation.
- Rule based risk scoring that is explainable and transparent.
- Streamlit dashboard design mirroring internal analyst tooling.
- Jupyter Notebook storytelling for interviews and walk-throughs.
- End-to-end workflow design from data creation to scoring to visualization.

**What you can review directly on GitHub:**

- Risk rules and scoring logic in `src/risk_rules.py`.
- Data generation workflow in `src/generate_synthetic_card_data.py`.
- Scored outputs and alerts in the `data/` folder.
- Full exploratory analysis notebook in `notebooks/card_fraud_analysis.ipynb`.
- Dashboard implementation in `dashboard/streamlit_app.py`.

---

## What this project does

This project is an end-to-end card fraud simulation designed to mirror the work of a payments risk analyst investigating CNP abuse, BIN anomalies, device/IP patterns, and chargeback risk.

---

### 1. Generates synthetic cardholders, merchants, and transactions

- Card profiles include BIN, brand, card type (credit, debit, prepaid), and home country.
- Merchants include MCC codes and country logic.
- Transactions include CNP vs card-present behavior, IP country, device ID, amount, timestamp, and authorization result.

---

### 2. Injects realistic card fraud patterns

- **Card testing behavior** (many small CNP authorizations across merchants).
- **High-risk BIN + high-risk MCC** combinations (prepaid + quasi cash, betting, direct marketing).
- **Geo mismatch CNP activity** (IP origin inconsistent with home country).
- **Amount spikes** on new or unusual merchants.
- **Device sharing patterns** suggesting account farms.
- **Chargeback-like behavior** to simulate loss recovery patterns.

---

### 3. Scores transactions with rule based detection

- Flags CNP high-amount transactions.
- Flags transactions in high-risk MCCs (5968, 4816, 7995, 6051).
- Elevates risk for prepaid BIN usage at sensitive merchants.
- Surfaces geo mismatch behavior.
- Flags devices used across many cardholders.
- Identifies card-testing velocity patterns.
- Produces a simple `risk_score` and list of triggered rules in `data/card_alerts.csv`.

---

### 4. Analyzes behavior in a notebook

- MCC-level fraud patterns and average risk.
- BIN behavior including prepaid risk.
- Geo mismatch concentrations.
- Device-level anomalies.
- Rule precision and performance measured against synthetic `is_fraud_pattern` labels.
- Chargeback correlation by risk bucket.

This notebook is designed to show how a card risk analyst thinks through fraud signals end-to-end.

---

### 5. Visualizes insights in a Streamlit dashboard

- Filters for risk score, MCC, brand, card type, and CNP vs card-present.
- Risk score distribution chart.
- MCC and BIN segments sorted by average risk.
- High-level KPIs (approval rate, fraud rate, chargeback rate, high-risk rate).
- Top high-risk cards.
- Devices associated with many high-risk cards.
- Rule-level alert counts and sample details.

---

## Tech stack

- **Python** for simulation and core logic.
- **pandas** for fraud analysis and transformations.
- **Jupyter Notebook** for exploration and explanation.
- **Streamlit** for the dashboard.
- **matplotlib** for charts in the notebook.

---

## Repository structure

```text
card-fraud-detection-simulator/
├─ data/
│  ├─ card_transactions.csv              # synthetic transactions (generated)
│  ├─ card_transactions_scored.csv       # transactions with risk_score (generated)
│  └─ card_alerts.csv                    # long table of rule hits (generated)
│
├─ src/
│  ├─ generate_synthetic_card_data.py    # builds cards, merchants, and transactions
│  ├─ risk_rules.py                      # rule based card fraud detection
│  └─ run_scoring.py                     # applies rules and writes outputs
│
├─ dashboard/
│  └─ streamlit_app.py                   # interactive card fraud dashboard
│
├─ notebooks/
│  └─ card_fraud_analysis.ipynb          # exploratory analysis and evaluation
│
└─ docs/
   └─ img/
      ├─ card_dashboard_1.png            # dashboard screenshots
      └─ card_dashboard_2.png
```

---

## How to review this project on GitHub without running anything

You can fully understand the system without running code:

1. **Review the rules**
   `src/risk_rules.py` shows each detection rule and how it contributes to risk scoring.

2. **Check the notebook**
   `notebooks/card_fraud_analysis.ipynb` walks through MCC patterns, BIN risk, geo mismatches, and rule performance.

3. **Scan the dashboard code**
   `dashboard/streamlit_app.py` shows how KPIs, charts, and filters connect to the underlying scoring logic.

4. **Browse the generated data**
   `data/card_transactions_scored.csv` includes risk scores, triggered rules, and synthetic chargeback flags.

This gives a complete picture of how a card fraud detection workflow functions end-to-end.

---

## How to run it locally (optional)

<details>
<summary>Setup and run instructions</summary>

### 1. Clone the repository

```bash
git clone https://github.com/cloudquiza/card-fraud-detection-simulator.git
cd card-fraud-detection-simulator
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install pandas numpy jupyter streamlit matplotlib
```

### 4. Generate synthetic data

```bash
python src/generate_synthetic_card_data.py
```

### 5. Score the transactions

```bash
python src/run_scoring.py
```

### 6. Launch the Streamlit dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

### 7. Open the notebook

```bash
jupyter notebook
```

---

</details>

---

## Why I built this

I created this project to practice thinking through card fraud using fresh, synthetic examples instead of relying only on older experience. Working through end-to-end workflows helps me explain risk concepts clearly in interviews, especially around CNP patterns, BIN/MCC behavior, device anomalies, and velocity signals.

I also used AI throughout the build, which made it easier to stay focused on understanding the fraud logic rather than boilerplate setup. Using AI feels increasingly expected in modern risk and fintech work, so it made sense to incorporate it into the process.

If you work in payments risk, fraud, trust and safety, or card issuing/acquiring and have feedback or ideas for extending this project, I would love to hear them.

---
