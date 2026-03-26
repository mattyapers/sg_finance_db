# SG Financial Dashboard

A Singapore-specific personal finance planner. Models salary budget, SRS tax relief, CPF, and long-term projections. Fully interactive — every input is a slider or number field.

## Features

- Monthly cash flow breakdown
- Expense tracker with add / remove rows
- SRS tax relief calculator (Singapore YA2026 brackets)
- SRS vs CPF SA long-term comparison chart
- Full gross income allocation view
- Adjustable CAGR, age, contribution levels
- Works for both SC/PR and foreigners

## Run locally

```bash
# 1. Clone or download this folder
cd sg_finance_dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Opens at http://localhost:8501

## Deploy to Streamlit Cloud (free, shareable link)

1. Push this folder to a GitHub repo (public or private)
2. Go to https://streamlit.io/cloud
3. Click **New app** → select your repo → set main file to `app.py`
4. Click **Deploy** — you get a public URL in ~60 seconds

Share the URL with anyone. No login required to view.

## Sidebar inputs

All inputs are in the sidebar. Fields start at zero — fill in your own numbers.

| Section | Input | Notes |
|---------|-------|-------|
| Income | Gross annual salary | Before CPF deduction |
| Income | Side income / month | Freelance, tutoring, etc. |
| Residency | SC/PR or Foreigner | Sets the SRS annual cap |
| Expenses | Any number of named rows | Click **＋ Add expense** to add; **✕** to remove |
| Investments | Core investing / month | ETFs, index funds, etc. |
| Investments | Satellite investing / month | Active picks |
| Investments | Savings / month | Emergency fund / buffer |
| SRS | Annual SRS contribution | Slider capped to your residency limit |
| SRS | Expected CAGR inside SRS | Adjustable 4–15% |
| SRS | Current age | Affects years-to-63 projection |

### Managing expense items

The expense section is fully flexible:
- **Add a row** — click **＋ Add expense** at the bottom of the expense list
- **Rename a row** — click into the label field and type
- **Remove a row** — click the **✕** button on that row

## Assumptions

- Singapore YA2026 tax brackets
- CPF employee contribution rate: 20%
- CPF ordinary wage ceiling: S$7,400/month (2025)
- Earned income relief: S$1,000
- SRS withdrawal at age 63, spread over 10 years
- 50% of each year's withdrawal is taxable
- Not financial advice
