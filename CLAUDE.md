# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install -r sg_finance_dashboard/requirements.txt
streamlit run sg_finance_dashboard/app.py
```

Opens at http://localhost:8501. There are no tests or lint commands.

## Architecture

Single-file Streamlit app (`app.py`). All logic is in one file — no modules, no imports from local packages.

**Data flow:**
1. Sidebar inputs (salary, expenses, SRS settings, residency) → reactive recalculation on every change
2. CPF deductions (20% employee rate, S$7,400/month OW ceiling)
3. Singapore YA2026 progressive tax brackets applied to chargeable income
4. SRS contribution reduces chargeable income → tax savings computed
5. Long-term projections to age 63 (SRS compound growth, CPF SA at 4% fixed)
6. All outputs rendered as Plotly charts + a summary dataframe

**Dynamic expense items:**
Expense rows in the sidebar are managed via `st.session_state.expense_items` (a list of `{"id": int, "label": str}`). Each row uses stable integer IDs as widget keys (`el_{id}`, `ev_{id}`) so values survive reruns. Add/remove buttons call `st.rerun()` after mutating the list. Values are read back from session_state keys, not from the list itself. All input defaults are set to 0 — no personal values are hardcoded.

**Key hardcoded assumptions:**
- CPF employee rate: 20%, OW ceiling S$7,400/month (2025)
- Earned income relief: S$1,000
- SRS caps: S$15,300 (SC/PR) vs S$35,700 (Foreigner)
- Retirement withdrawal model: 50% of annual withdrawal taxable, spread over 10 years at age 63
- CPF SA comparison benchmark: 4% guaranteed

**Chart color palette** (used consistently across all Plotly figures):
- Expenses: `#D85A30`, Core investing: `#185FA5`, Satellite: `#1D9E75`
- Savings: `#639922`, SRS: `#BA7517`, CPF: `#888780`, Buffer: `#B4B2A9`

## Code Style

Use comments sparingly. Only comment on non-obvious logic (e.g. tax bracket edge cases, CPF ceiling math) and to mark areas where UI, UX, or features could be extended.

## Deployment

Push to GitHub, connect at https://streamlit.io/cloud — no configuration needed beyond the requirements file.
