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
- **40 classroom sessions** scheduled: 30 teaching sessions (Mon/Tue/Wed, 18:00–20:00 WAT) + 10 Friday office hours (18:00–19:00 WAT), from Mon 5 Oct 2026
- Plans **Pay in Full** ($200) and **Pay in 2 Installments** ($110 + $110 = $220)
- Seed script reminder to enable `BILLING_PLANS_ENABLED=true`

Idempotent: safe to re-run; existing plans are left in place (installment due date may be refreshed). Sessions are matched on type + number and updated in place; use `--reset` to wipe the cohort's sessions and rebuild them.

## 2. Enable billing plans + live payments

On the **Render API service → Environment**:

| Key | Value |
|-----|--------|
| `BILLING_PLANS_ENABLED` | `true` |
| `PAYMENT_MODE` | `live` |

Also set live provider secrets (empty keys still mock out even when mode is `live`):

| Key | Notes |
|-----|--------|
| `PAYSTACK_SECRET_KEY` | Live `sk_live_…` |
| `PAYSTACK_CHARGE_CURRENCY` | Usually `NGN` for NG merchants |
| `PAYSTACK_USD_TO_NGN_RATE` | Used when catalogue prices are USD |
| `NOWPAYMENTS_API_KEY` | Live crypto invoices |
| `NOWPAYMENTS_IPN_SECRET` | IPN signing secret |
| `PUBLIC_API_URL` | HTTPS API origin (webhook base) |
| `FRONTEND_URL` | HTTPS site origin |

Webhook / IPN URLs in provider dashboards:

- Paystack: `{PUBLIC_API_URL}/api/v1/webhooks/payments/paystack`
- NOWPayments: `{PUBLIC_API_URL}/api/v1/webhooks/payments/nowpayments`

`PUBLIC_API_URL` must be the public **HTTPS** API origin — NOWPayments cannot deliver IPN callbacks to localhost or unreachable hosts. The invoice stores the IPN URL at creation time, so deploy the env change **before** students pay.

### NOWPayments IPN delivery verification

The IPN is the only thing that flips a payment from `pending` to `confirmed` automatically. After any live crypto payment:

1. **Check the API logs** — every IPN attempt logs either `Webhook processed` (200) or an error (401 bad signature, 404 unknown order, 503 missing IPN secret).
2. **Check the DB** — a processed IPN inserts a row into `payment_webhook_events`:
   ```sql
   SELECT provider, event_key, payment_id, created_at
   FROM payment_webhook_events
   WHERE provider = 'nowpayments'
   ORDER BY created_at DESC LIMIT 10;
   ```
3. If the payment is `finished` in the NOWPayments dashboard but there is **no** IPN log/row, the callback never arrived — in order of likelihood:
   - `PUBLIC_API_URL` is unset/localhost/wrong host (see startup warnings — the app logs a warning at boot when NOWPayments is live but `PUBLIC_API_URL` is not public HTTPS).
   - `NOWPAYMENTS_IPN_SECRET` does not match the dashboard secret (every IPN gets a 401).
   - A firewall/Cloudflare rule is blocking NOWPayments' IPs (allowlist required — request their IP list from NOWPayments support).
4. The NOWPayments dashboard can **resend** the IPN for a payment (and retry settings live under Settings → Payments → Instant Payment Notifications — raise the recurrent-notification count/timeout so transient API errors recover on their own).

**Self-healing built into the app:** reading a stuck NOWPayments payment (`GET /api/v1/payments/{order_id}` — the success page polls this every 4 s, and admin payments reads also trigger it) auto-pulls the real status from NOWPayments once the payment is older than ~90 s, throttled to one lookup per minute. So even a missed IPN reconciles itself within one poll cycle.

**Admin fallback:** `/admin/payments` → Reconcile. It now auto-discovers the payment by our `order_id`; the manual "payment ID" input only appears if discovery finds nothing (e.g. customer paid with an unmapped address).

Save and **deploy** so the running process reloads settings.

Local / staging rehearsal: keep `PAYMENT_MODE=mock` until the plan picker and unlock path look correct.

### Cohort registration window (BDE seed)

`seed_blockchain_data_engineering.py` currently sets:

- Registration open from **4 Sep 2026** (cohort status `OPEN`)
- Registration deadline **3 Oct 2026** 23:59 UTC
- Programme start **6 Oct 2026**, end **14 Dec 2026** (10 weeks)

Re-run both seed scripts on Render after pulling this change so production dates update.

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
- [ ] `PAYMENT_MODE=live` deployed on API (with live Paystack / NOWPayments secrets + webhooks)
- [ ] `PUBLIC_API_URL` is the public HTTPS API origin (NOWPayments IPN base)
- [ ] Test crypto payment IPN visible in `payment_webhook_events` and logs  
- [ ] `verify_bde_checkout.py` exits 0 and prints `PAYMENT_MODE: live`  
- [ ] Public cohorts API includes BDE as `open`  
- [ ] Billing plans API returns both plans  
- [ ] Checkout UI shows plan chooser  
- [ ] One live (or test-key) enrollment completed (full + installments if possible)  

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Checkout: “Cohort not available” | Cohort missing or not `open`/`active` in DB; re-run BDE seed |
| Checkout: single price, no plans | `BILLING_PLANS_ENABLED` false or not redeployed; or plans never seeded |
| Checkout: “Select a tuition plan” API error | Flag on and plans exist, but client omitted `tuition_plan_id` |
| Plans API always `[]` | Flag off |
| “Registration has closed” | `registration_deadline` in the past; refresh via BDE seed |
