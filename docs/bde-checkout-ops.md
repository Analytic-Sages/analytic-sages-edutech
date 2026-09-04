# BDE checkout & tuition plans (production ops)

Blockchain Data Engineering (`blockchain-data-engineering`) registration and flexible tuition need both **data** and a **feature flag**. Marketing can say “open” while checkout still fails until this checklist is green.

## Safe order (avoid a broken window)

1. Seed / refresh the cohort as `OPEN`
2. Seed tuition plans (Pay in Full + 2 installments)
3. Set `BILLING_PLANS_ENABLED=true` on the API service and deploy
4. Run the verify script (and optional public HTTP checks)
5. Do one end-to-end test enrollment before sending real students

## 1. Seed on Render (API service)

Use an **ephemeral shell** or **one-off job** on the production API service so you get the same env and database as live traffic. Working directory should be the backend app root (where `scripts/` and `app/` live).

```bash
python scripts/seed_blockchain_data_engineering.py
python scripts/seed_tuition_plans.py
```

Expected:

- Cohort `blockchain-data-engineering` created or updated with status **open**, price **$200**
- Plans **Pay in Full** ($200) and **Pay in 2 Installments** ($110 + $110 = $220)
- Seed script reminder to enable `BILLING_PLANS_ENABLED=true`

Idempotent: safe to re-run; existing plans are left in place (installment due date may be refreshed).

## 2. Enable billing plans

On the **Render API service → Environment**:

| Key | Value |
|-----|--------|
| `BILLING_PLANS_ENABLED` | `true` |

Save and **deploy** so the running process reloads settings. Default in code is `false` (legacy one-time checkout only; `/api/v1/billing/plans` returns `[]`).

Related (local / staging):

- Prefer `PAYMENT_MODE=mock` for rehearsal without real money
- Live Paystack / NOWPayments only after mock path looks correct

## 3. Verify (database + flag)

From the same backend environment:

```bash
python scripts/verify_bde_checkout.py
```

Exit code `0` = ready. Non-zero = fix the printed failures before marketing traffic hits checkout.

Optional public HTTP checks (replace host and cohort id):

```bash
# Must list BDE with status open
curl -sS "$PUBLIC_API_URL/api/v1/public/cohorts" | jq '.[] | select(.slug=="blockchain-data-engineering")'

# Must return both tuition plans when the flag is on
curl -sS "$PUBLIC_API_URL/api/v1/billing/plans?cohort_id=<COHORT_UUID>"
```

Browser: `/checkout/cohort/blockchain-data-engineering` should show **Choose a tuition plan**, not “Cohort not available” and not a bare one-time price only.

## 4. Confidence that installments work

### Automated

```bash
cd backend
pytest tests/test_tuition_billing.py -q
```

Covers: schedule sums, obligation generation, checkout requires a plan when the flag is on, first payment unlocks seat + duplicate webhook safety, failed attempt reopens obligation, legacy one-time when the flag is off.

### Manual / staging rehearsal

| Step | Pass when |
|------|-----------|
| Pay in Full | Charged full amount; seat unlocked; no open installment left |
| Pay in 2 (first) | Charged first installment only; seat unlocked; Billing shows remaining |
| Pay in 2 (second) | Paid from **Billing** (not Join again); obligation paid; outstanding 0 |
| Admin | `/admin/billing` and `/admin/payments` show account + attempt |
| Flag off regression | With flag false and no reliance on plans, legacy one-time still works |

Product behaviour in this release: seat unlocks after the **first** confirmed payment; later installments are tracked on Billing and are **not** designed to auto-revoke access if missed.

## 5. Done checklist

- [ ] `seed_blockchain_data_engineering.py` run on production DB  
- [ ] `seed_tuition_plans.py` run on production DB  
- [ ] `BILLING_PLANS_ENABLED=true` deployed on API  
- [ ] `verify_bde_checkout.py` exits 0  
- [ ] Public cohorts API includes BDE as `open`  
- [ ] Billing plans API returns both plans  
- [ ] Checkout UI shows plan chooser  
- [ ] One mock or test-account enrollment completed (full + installments if possible)  

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Checkout: “Cohort not available” | Cohort missing or not `open`/`active` in DB; re-run BDE seed |
| Checkout: single price, no plans | `BILLING_PLANS_ENABLED` false or not redeployed; or plans never seeded |
| Checkout: “Select a tuition plan” API error | Flag on and plans exist, but client omitted `tuition_plan_id` |
| Plans API always `[]` | Flag off |
| “Registration has closed” | `registration_deadline` in the past; refresh via BDE seed |
