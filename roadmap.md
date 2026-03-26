# SG Finance Dashboard — Roadmap

## Done
- [x] Single-file Streamlit app with sidebar inputs
- [x] CPF deduction and Singapore YA2026 progressive tax brackets
- [x] SRS tax relief calculator with compound growth projection
- [x] SRS vs CPF SA side-by-side comparison chart
- [x] Monthly cash flow breakdown (bar) + expense breakdown (donut)
- [x] Full gross income allocation chart
- [x] Dynamic expense rows — add, rename, remove without page reload
- [x] Residency toggle (SC/PR vs Foreigner) with correct SRS cap
- [x] All input defaults set to neutral values (no personal figures)

## Done (continued)
- [x] Savings rate metric — specific tooltip formula + raw S$/mo delta
- [x] Monthly buffer metric — tooltip with thresholds + over-allocated state
- [x] Tax metrics — tax before SRS, tax after SRS, and tax saved as separate metrics
- [x] Chart colour palette — Tailwind 600-level palette (red, blue, emerald, violet, amber, grey)

## Backlog

### UX / interactivity
- [ ] Shareable URL state — encode sidebar inputs into query params so a URL reproduces a specific scenario
- [ ] Preset scenarios — e.g. "Fresh grad", "Mid-career", "Max SRS" buttons that populate all fields at once
- [ ] Dark mode support

### Data & calculations
- [ ] CPF employer contribution — show gross cost to employer alongside employee take-home
- [ ] CPF SA voluntary top-up — model the additional 4% compounding alongside SRS
- [ ] Bonus income — one-time annual input that feeds into tax calculation separately
- [ ] Multi-year salary growth — model salary increasing at a user-set rate over the projection horizon
- [ ] Inflation-adjusted projections — toggle to show SRS / CPF values in today's dollars

### Output / export
- [ ] Export summary to PDF or CSV
- [ ] Print-friendly layout

### Deployment
- [ ] Add st.secrets / environment variable support for any future API keys
- [ ] Pin dependency versions in requirements.txt
