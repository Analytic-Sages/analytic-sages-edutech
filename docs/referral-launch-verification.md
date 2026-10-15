# Referral Partner Launch Verification

This runbook supplements `backend/tests/test_referral_partners.py`. Automated tests should run against the CI test database; do not use real customer payments to prove financial flows.

## Automated verification

From the repository root:

```bash
cd backend
pytest -q tests/test_referral_partners.py
```

The regression suite covers:
- 7% payment-level commission creation and duplicate-webhook idempotency.
- Two confirmed $28 installments each generating one $1.96 commission.
- First-touch attribution and the 30-day visitor cookie.
- Cookie attribution being locked to a newly registered account, so a later payment from another device can resolve the account-level attribution.
- Pending refund voiding, hold release, and refunds overlapping an open payout.
- Minimum payout rejection in USD and NGN.
- Public leaderboard response serialization and private-field exclusion.
- Existing currency reporting and unsupported-currency checks.

## Manual browser checks before enabling public applications

1. In a staging deployment with the partner flag disabled, verify anonymous access to `/partners` and the public leaderboard is blocked; admin preview still works.
2. Create an active test partner. Open `/ref/{code}` in a fresh browser profile and confirm the `as_ref_vid` cookie is set with `Path=/`, `HttpOnly`, `SameSite=Lax`, and a 30-day `Max-Age` (2,592,000 seconds).
3. Close and reopen the browser, register a new learner, and confirm the attribution is locked to that user. Sign in on a separate browser/device and pay from the learner account; confirm the commission is assigned to the original partner.
4. Use a staging payment provider/test mode to confirm two separate $28 payments produce exactly two $1.96 commission rows and ledger entries—not one combined or duplicated commission.
5. Refund a payment during the hold: the pending commission and corresponding pending ledger entry must be voided. Release an unrefunded commission after the hold and verify it becomes available.
6. Refund an available commission with no open payout and verify a reversal is recorded. Repeat with an open payout request: the conversion must enter review-required and the payout must not transition to processing/paid.
7. Try payout requests below the configured threshold for every enabled currency and confirm they are rejected. Test at/above the minimum only with a funded staging ledger.
8. Open the public leaderboard with the flag enabled. Inspect the raw API response in browser developer tools: it must contain only `rank`, `display_name`, and `successful_enrollments` per row.
9. Complete one end-to-end staging transaction, inspect the partner dashboard and admin referrals panel, then refund it and verify the ledger/audit trail. Never use a real learner payment or initiate a real payout just for this test.

## Release gate

Do not enable `NEXT_PUBLIC_PARTNERS_PUBLIC=true` in production until CI passes, the staging checks above are recorded, payout/refund edge cases are resolved, and the team has confirmed manual payout operations and refund policy alignment. Because the frontend flag is baked in at build time, changing it requires a new frontend deployment. Backend visibility checks must remain enabled regardless of frontend navigation/robots settings.
