# Personal Finance Dashboard

A Streamlit dashboard that reads the "Main" tab of a personal balance tracker workbook (.xlsx) and renders a dark, fintech-style view of your finances:

- Net worth composition (cash vs investments) and liquidity ratio
- Investment platform performance (Hargreaves Lansdown, Trading 212, Crypto)
- Current account breakdown, credit card exposure, wage vs needed
- Mortgage and debt payoff progress, plus "fun balance"

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run balance_dashboard.py
```

Then upload your balance tracker workbook (.xlsx) using the sidebar uploader.

## Workbook expectations

- A sheet named `Main`
- Two header rows (skipped on load); dates in column A (day-first format)
- Column positions are mapped in `COL_MAP` at the top of the data-loading section of `balance_dashboard.py`. If you add or move columns in your workbook, update that mapping.

## Privacy

Your workbook is processed locally and is never stored by the app. Do not commit your `.xlsx` file to this repo: the `.gitignore` excludes spreadsheets by default.
