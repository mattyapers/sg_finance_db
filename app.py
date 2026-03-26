"""
Singapore Financial Dashboard
==============================
A personal finance planner built for Singapore residents.
Models salary budget, SRS tax relief, CPF, and long-term projections.

Run:  streamlit run app.py
Deploy: https://streamlit.io/cloud (free)
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="SG Finance Dashboard",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colour palette (consistent across all charts)
C = {
    "expenses":  "#DC2626",   # red-600
    "core":      "#2563EB",   # blue-600
    "satellite": "#059669",   # emerald-600
    "savings":   "#7C3AED",   # violet-600
    "srs":       "#D97706",   # amber-600
    "buffer":    "#9CA3AF",   # gray-400
    "cpf":       "#4B5563",   # gray-600
    "bg":        "#F8F7F4",
    "accent":    "#1E3A5F",
}

# Cycling palette for dynamic expense slices in the pie chart
EXPENSE_PALETTE = [
    "#DC2626", "#2563EB", "#059669",
    "#7C3AED", "#D97706", "#0891B2", "#9CA3AF",
]

# ─── Session state: dynamic expense items ────────────────────────────────────
# Each item has a stable integer ID used as a widget key so values survive reruns.
# UI extension point: could load/save expense presets to a config file or URL params.
if "expense_items" not in st.session_state:
    st.session_state.expense_items = [
        {"id": 1, "label": "Rent / mortgage"},
        {"id": 2, "label": "Transport"},
        {"id": 3, "label": "Food & dining"},
        {"id": 4, "label": "Utilities"},
    ]
    st.session_state._next_expense_id = 5

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR — all inputs live here
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## Your inputs")
    st.markdown("---")

    st.markdown("**Income**")
    gross_salary   = st.number_input("Gross annual salary (S$)", 0, 300_000, 60_000, 1_000)
    side_income_mo = st.number_input("Side income / month (S$)", 0, 10_000, 0, 50)

    st.markdown("---")
    st.markdown("**Residency**")
    # Must appear before SRS slider so srs_cap can set the correct max
    status  = st.selectbox("Residency status", ["Singapore Citizen / PR", "Foreigner"])
    srs_cap = 15_300 if status == "Singapore Citizen / PR" else 35_700
    st.caption(f"SRS annual cap: **S${srs_cap:,}**")

    st.markdown("---")
    st.markdown("**Monthly expenses**")

    # Dynamic expense rows: label (editable) | amount | remove button
    # UI extension point: add drag-to-reorder, category tags, or recurring vs one-off flags
    to_delete = None
    for item in st.session_state.expense_items:
        uid = item["id"]
        col_l, col_v, col_d = st.columns([2, 1.5, 0.4])
        with col_l:
            st.text_input(
                "Label", key=f"el_{uid}",
                value=item["label"],
                label_visibility="collapsed",
            )
        with col_v:
            st.number_input(
                "S$", 0, 10_000, 0, 10,
                key=f"ev_{uid}",
                label_visibility="collapsed",
            )
        with col_d:
            if st.button("✕", key=f"ed_{uid}", help="Remove"):
                to_delete = uid

    if to_delete is not None:
        st.session_state.expense_items = [
            x for x in st.session_state.expense_items if x["id"] != to_delete
        ]
        for k in [f"el_{to_delete}", f"ev_{to_delete}", f"ed_{to_delete}"]:
            st.session_state.pop(k, None)
        st.rerun()

    if st.button("＋ Add expense"):
        new_id = st.session_state._next_expense_id
        st.session_state._next_expense_id += 1
        st.session_state.expense_items.append({"id": new_id, "label": "New item"})
        st.rerun()

    # Collect current values from widget keys (which hold whatever the user typed/set)
    expense_items = {
        st.session_state.get(f"el_{item['id']}", item["label"]): st.session_state.get(f"ev_{item['id']}", 0)
        for item in st.session_state.expense_items
    }
    total_expenses = sum(expense_items.values())

    st.markdown("---")
    st.markdown("**Investment allocations**")
    core_invest_mo = st.number_input("Core investing / month (S$)", 0, 5_000, 0, 50)
    sat_invest_mo  = st.number_input("Satellite investing / month (S$)", 0, 2_000, 0, 50)
    savings_mo     = st.number_input("Savings / month (S$)", 0, 5_000, 0, 50)

    st.markdown("---")
    st.markdown("**SRS settings**")
    srs_annual  = st.slider("Annual SRS contribution (S$)", 0, srs_cap, 0, 100)
    cagr_pct    = st.slider("Expected CAGR inside SRS (%)", 4.0, 15.0, 8.0, 0.5)
    current_age = st.slider("Current age", 22, 55, 30)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALCULATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# CPF: employee 20%, capped at OW ceiling S$7,400/mo (2025)
monthly_salary = gross_salary / 12
ow_ceiling     = 7_400
cpf_monthly    = min(monthly_salary, ow_ceiling) * 0.20
take_home_mo   = monthly_salary - cpf_monthly + side_income_mo

# Singapore YA2026 progressive tax brackets
def calc_tax(chargeable_income: float) -> float:
    brackets = [
        (20_000, 0.00),
        (10_000, 0.02),
        (10_000, 0.035),
        (40_000, 0.07),
        (40_000, 0.115),
        (40_000, 0.15),
        (40_000, 0.18),
        (40_000, 0.19),
        (40_000, 0.195),
        (40_000, 0.20),
        (float("inf"), 0.22),
    ]
    tax, remaining = 0.0, chargeable_income
    for band, rate in brackets:
        if remaining <= 0:
            break
        taxable = min(remaining, band)
        tax += taxable * rate
        remaining -= taxable
    return tax

cpf_annual       = cpf_monthly * 12
earned_relief    = 1_000
ci_before_srs    = max(0, gross_salary - cpf_annual - earned_relief)
ci_after_srs     = max(0, ci_before_srs - srs_annual)

tax_before       = calc_tax(ci_before_srs)
tax_after        = calc_tax(ci_after_srs)
tax_saved_annual = tax_before - tax_after
tax_saved_mo     = tax_saved_annual / 12

# Marginal rate approximation; fall back to lowest bracket when SRS is 0
marginal_rate    = tax_saved_annual / srs_annual if srs_annual > 0 else 0.0

savings_rate     = (take_home_mo - total_expenses) / take_home_mo if take_home_mo > 0 else 0
total_deployed   = total_expenses + core_invest_mo + sat_invest_mo + savings_mo + (srs_annual / 12)
buffer_mo        = take_home_mo - total_deployed

# SRS compound growth to retirement age 63
retirement_age    = 63
years_to_retire   = max(retirement_age - current_age, 1)
r                 = cagr_pct / 100
srs_fv            = srs_annual * ((pow(1 + r, years_to_retire) - 1) / r) if srs_annual > 0 else 0
total_contributed = srs_annual * years_to_retire
total_tax_saved   = tax_saved_annual * years_to_retire
net_cost          = total_contributed - total_tax_saved

# Withdrawal model: 50% taxable, spread over 10 years at age 63
annual_withdrawal  = srs_fv / 10
taxable_per_yr     = annual_withdrawal * 0.50
withdrawal_tax     = calc_tax(taxable_per_yr) * 10
net_srs_after_tax  = srs_fv - withdrawal_tax

if net_cost > 0 and years_to_retire > 0:
    eff_return = (pow(net_srs_after_tax / net_cost, 1 / years_to_retire) - 1) * 100
else:
    eff_return = 0.0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("💹 SG Financial Dashboard")
st.caption("Singapore salary budget optimiser · SRS tax planner · long-term projections")

# Hero metrics
raw_saving = take_home_mo - total_expenses

if buffer_mo > 150:
    buf_label, buf_color = "healthy", "normal"
elif buffer_mo >= 0:
    buf_label, buf_color = "thin", "off"
else:
    buf_label, buf_color = "over-allocated", "inverse"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Take-home / mo", f"S${take_home_mo:,.0f}", help="After CPF deduction + side income")
c2.metric(
    "Savings rate", f"{savings_rate:.1%}",
    delta=f"S${raw_saving:,.0f} / mo",
    delta_color="normal",
    help="(Take-home − total expenses) ÷ take-home",
)
c3.metric(
    "Monthly buffer", f"S${buffer_mo:,.0f}",
    delta=buf_label,
    delta_color=buf_color,
    help=(
        "What remains after all planned spending and investments. "
        "Healthy = S$150+/mo · Thin = S$0–149 · Over-allocated = negative "
        "(planned outflows exceed take-home)."
    ),
)
c4.metric(
    "Tax (no SRS)", f"S${tax_before:,.0f}",
    help="Annual income tax before any SRS contribution",
)
c5.metric(
    "Tax (with SRS)", f"S${tax_after:,.0f}",
    delta=f"−S${tax_saved_annual:,.0f} saved",
    delta_color="inverse",
    help=f"After S${srs_annual:,} SRS contribution · Marginal rate: {marginal_rate:.1%}",
)
c6.metric(
    f"SRS value at {retirement_age}", f"S${srs_fv/1000:,.0f}k",
    help=f"{years_to_retire} years at {cagr_pct}% CAGR",
)

st.markdown("---")

# ── Row 1: Budget + expenses ──────────────────────────────────────────────
col_left, col_right = st.columns([1.4, 1])

with col_left:
    st.markdown("#### Monthly cash flow")

    budget_labels = ["Expenses", "Core investing", "Satellite", "Savings", "SRS (monthly)", "Buffer"]
    budget_values = [
        total_expenses,
        core_invest_mo,
        sat_invest_mo,
        savings_mo,
        srs_annual / 12,
        max(buffer_mo, 0),
    ]
    budget_colors = [C["expenses"], C["core"], C["satellite"], C["savings"], C["srs"], C["buffer"]]

    fig_budget = go.Figure(go.Bar(
        x=budget_values,
        y=budget_labels,
        orientation="h",
        marker_color=budget_colors,
        text=[f"S${v:,.0f}" for v in budget_values],
        textposition="outside",
        cliponaxis=False,
    ))
    fig_budget.update_layout(
        height=280, margin=dict(l=0, r=60, t=10, b=10),
        xaxis=dict(title="S$ / month", gridcolor="#EEEEEE"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    st.plotly_chart(fig_budget, use_container_width=True)

with col_right:
    st.markdown("#### Expense breakdown")

    exp_labels = list(expense_items.keys())
    exp_values = list(expense_items.values())
    n_slices   = max(len(exp_values), 1)
    pie_colors = [EXPENSE_PALETTE[i % len(EXPENSE_PALETTE)] for i in range(n_slices)]

    fig_pie = go.Figure(go.Pie(
        labels=exp_labels,
        values=exp_values,
        hole=0.5,
        marker_colors=pie_colors,
        textinfo="label+percent",
        textfont_size=11,
    ))
    fig_pie.update_layout(
        height=280, margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(text=f"S${total_expenses:,.0f}<br>/mo", x=0.5, y=0.5,
                          font_size=13, showarrow=False)]
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ── Row 2: SRS deep dive ─────────────────────────────────────────────────
st.markdown("#### SRS projection")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total contributed", f"S${total_contributed/1000:,.1f}k",
          help=f"S${srs_annual:,}/yr × {years_to_retire} years")
c2.metric("Total tax saved", f"S${total_tax_saved:,.0f}",
          help="Tax relief compounded over contribution period")
c3.metric("Net withdrawal cost", f"S${net_cost/1000:,.1f}k",
          help="Total contributed minus all tax savings")
c4.metric("Effective net return", f"{eff_return:.1f}%",
          help="CAGR on your actual out-of-pocket cost, after withdrawal tax")

years_range    = list(range(1, years_to_retire + 1))
fv_series      = [srs_annual * ((pow(1 + r, y) - 1) / r) if srs_annual > 0 else 0 for y in years_range]
contrib_series = [srs_annual * y for y in years_range]
tax_series     = [tax_saved_annual * y for y in years_range]

df_proj = pd.DataFrame({
    "year": [current_age + y for y in years_range],
    "SRS value": fv_series,
    "Total contributed": contrib_series,
    "Cumulative tax saved": tax_series,
})

fig_srs = go.Figure()
fig_srs.add_trace(go.Scatter(
    x=df_proj["year"], y=df_proj["SRS value"],
    name="SRS value", fill="tozeroy",
    line=dict(color=C["srs"], width=2),
    fillcolor="rgba(217,119,6,0.10)",
))
fig_srs.add_trace(go.Scatter(
    x=df_proj["year"], y=df_proj["Total contributed"],
    name="Total contributed",
    line=dict(color=C["core"], width=1.5, dash="dash"),
))
fig_srs.add_trace(go.Scatter(
    x=df_proj["year"], y=df_proj["Cumulative tax saved"],
    name="Cumulative tax saved",
    line=dict(color=C["savings"], width=1.5, dash="dot"),
))
fig_srs.update_layout(
    height=320, margin=dict(l=0, r=0, t=10, b=10),
    xaxis=dict(title="Age", gridcolor="#EEEEEE"),
    yaxis=dict(title="S$", gridcolor="#EEEEEE", tickformat=",.0f"),
    plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    hovermode="x unified",
)
st.plotly_chart(fig_srs, use_container_width=True)

st.markdown("---")

# ── Row 3: Tax comparison + gross allocation ──────────────────────────────
col_tax, col_gross = st.columns([1, 1.3])

with col_tax:
    st.markdown("#### Tax impact of SRS")

    fig_tax = go.Figure(go.Bar(
        x=["Without SRS", "With SRS"],
        y=[tax_before, tax_after],
        marker_color=[C["expenses"], C["savings"]],
        text=[f"S${tax_before:,.0f}", f"S${tax_after:,.0f}"],
        textposition="outside",
    ))
    fig_tax.add_annotation(
        x=0.5, y=max(tax_before, tax_after) * 1.1,
        text=f"<b>Save S${tax_saved_annual:,.0f}/yr</b>",
        showarrow=False, font=dict(size=13, color=C["savings"]),
        xref="paper",
    )
    fig_tax.update_layout(
        height=280, margin=dict(l=0, r=0, t=30, b=10),
        yaxis=dict(title="Annual tax (S$)", gridcolor="#EEEEEE"),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_tax, use_container_width=True)

with col_gross:
    st.markdown("#### Where every gross dollar goes")

    gross_annual  = gross_salary + side_income_mo * 12
    alloc_labels  = ["CPF (employer not incl.)", "Expenses", "Core investing",
                     "Satellite", "Savings", "SRS", "Buffer"]
    alloc_values  = [
        cpf_annual,
        total_expenses * 12,
        core_invest_mo * 12,
        sat_invest_mo * 12,
        savings_mo * 12,
        srs_annual,
        max(buffer_mo, 0) * 12,
    ]
    alloc_colors  = [C["cpf"], C["expenses"], C["core"],
                     C["satellite"], C["savings"], C["srs"], C["buffer"]]

    fig_gross = go.Figure(go.Bar(
        x=alloc_labels,
        y=[v / gross_annual * 100 for v in alloc_values] if gross_annual > 0 else [0] * len(alloc_values),
        marker_color=alloc_colors,
        text=[f"{v/gross_annual:.1%}" for v in alloc_values] if gross_annual > 0 else ["0%"] * len(alloc_values),
        textposition="outside",
        cliponaxis=False,
    ))
    fig_gross.update_layout(
        height=280, margin=dict(l=0, r=0, t=30, b=10),
        yaxis=dict(title="% of gross income", gridcolor="#EEEEEE"),
        xaxis=dict(tickangle=-20),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_gross, use_container_width=True)

st.markdown("---")

# ── Row 4: SRS vs CPF SA comparison ─────────────────────────────────────
st.markdown("#### SRS vs CPF SA top-up — side-by-side")

# CPF SA at 4% guaranteed rate used as benchmark
yrs      = list(range(1, years_to_retire + 1))
srs_vals = [srs_annual * ((pow(1.0 + r, y) - 1) / r) if srs_annual > 0 else 0 for y in yrs]
cpf_vals = [srs_annual * ((pow(1.04, y) - 1) / 0.04) if srs_annual > 0 else 0 for y in yrs]
ages     = [current_age + y for y in yrs]

fig_cmp = go.Figure()
fig_cmp.add_trace(go.Scatter(
    x=ages, y=srs_vals,
    name=f"SRS @ {cagr_pct}% (invested)",
    line=dict(color=C["srs"], width=2),
    fill="tozeroy", fillcolor="rgba(217,119,6,0.08)",
))
fig_cmp.add_trace(go.Scatter(
    x=ages, y=cpf_vals,
    name="CPF SA @ 4% (guaranteed)",
    line=dict(color=C["cpf"], width=2, dash="dash"),
))
advantage = srs_vals[-1] - cpf_vals[-1]
fig_cmp.add_annotation(
    x=ages[-1], y=srs_vals[-1],
    text=f" SRS advantage: S${advantage/1000:,.0f}k at {retirement_age}",
    showarrow=False, font=dict(size=12, color=C["srs"]),
    xanchor="right",
)
fig_cmp.update_layout(
    height=300, margin=dict(l=0, r=0, t=10, b=10),
    xaxis=dict(title="Age", gridcolor="#EEEEEE"),
    yaxis=dict(title="S$", gridcolor="#EEEEEE", tickformat=",.0f"),
    plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    hovermode="x unified",
)
st.plotly_chart(fig_cmp, use_container_width=True)

# ── Footer summary table ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Full summary")

summary_data = {
    "Metric": [
        "Gross salary (annual)", "Side income (annual)", "CPF contribution (annual)",
        "Chargeable income (before SRS)", "SRS contribution (annual)",
        "Chargeable income (after SRS)", "Tax without SRS", "Tax with SRS",
        "Annual tax saving", "Take-home per month", "Total expenses per month",
        "Core investing per month", "Satellite per month", "Savings per month",
        "Monthly buffer", "Savings rate",
    ],
    "Value": [
        f"S${gross_salary:,.0f}", f"S${side_income_mo*12:,.0f}", f"S${cpf_annual:,.0f}",
        f"S${ci_before_srs:,.0f}", f"S${srs_annual:,.0f}",
        f"S${ci_after_srs:,.0f}", f"S${tax_before:,.0f}", f"S${tax_after:,.0f}",
        f"S${tax_saved_annual:,.0f}", f"S${take_home_mo:,.0f}", f"S${total_expenses:,.0f}",
        f"S${core_invest_mo:,.0f}", f"S${sat_invest_mo:,.0f}", f"S${savings_mo:,.0f}",
        f"S${buffer_mo:,.0f}", f"{savings_rate:.1%}",
    ],
}
st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

st.caption(
    "Assumptions: Singapore YA2026 tax brackets · CPF employee rate 20% · OW ceiling S$7,400/mo · "
    "SRS withdrawal at 63 over 10 years · 50% of withdrawal is taxable · "
    "Earned income relief S$1,000 applied. This is not financial advice."
)
