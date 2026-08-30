# RecoveryOS — AI Revenue Recovery Autopilot

Razorpay AI Buildathon — Track 3 submission. See the full spec this scaffold
was built from for the complete feature list and priorities (P0/P1/P2).

## Status

This is the initial scaffold: the P0 backbone runs end-to-end on a seeded
synthetic dataset (10,000 events) —

Risk detection → Decision Engine (expected-value action selection) →
Policy Engine (retry limits, budget, authorization, human-approval
threshold) → Simulation Adapter → Audit Ledger → batch metrics.

Verified working via a local smoke test (2,000-event batch): ~19% at-risk,
~53% of at-risk revenue recovered, sensible per-transaction audit trails,
and two Recovery Playbook strategies discovered.

**Not yet built:** transaction detail page, "Why this action?" panel,
what-if UI (API endpoint exists, no frontend yet), policy settings screen,
real Razorpay test-mode wiring (adapter is stubbed — see
`backend/app/adapters/razorpay_adapter.py` for TODOs), premium dashboard
styling (`frontend-design` skill hasn't been applied yet — current UI is a
functional placeholder only).

## Project structure

```
backend/
  app/
    models/      Pydantic schemas (PaymentEvent, Policy, RecoveryDecision, ...)
    engine/       risk_predictor, decision_engine, policy_engine, playbook,
                  audit_ledger, orchestrator (wires it all together)
    adapters/     RecoveryActionAdapter interface + Razorpay + Simulation impls
    data/         synthetic_generator.py (seeded batch of payment events)
    api/          FastAPI routes
    main.py       FastAPI app entrypoint
frontend/
  src/
    api/client.js
    pages/Dashboard.jsx   overview stats + RUN RECOVERY AUTOPILOT
    App.jsx, main.jsx
```

## Running it

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Then open the Vite dev server URL — it proxies `/api` to `localhost:8000`.

## Design notes / decisions baked into this scaffold

- **RETRY is only a candidate action when `mandate_available` is true.**
  This is the "never arbitrarily debit" boundary from the spec, enforced
  in both `decision_engine._candidate_actions` and again defensively in
  `policy_engine.check` and `RazorpayAdapter.execute`.
- **All financial actions pass through `policy_engine.check`** before
  execution — retry limits, recovery budget, feature toggles, contact-
  attempt caps, and the human-approval threshold are all deterministic
  checks, not LLM judgment calls.
- **Every stage writes to `AuditLedger`**, so the full per-transaction
  timeline (spec §14) can be reconstructed via `GET /api/recovery/audit/{id}`.
- **Simulated vs. real actions are labeled at the data level**
  (`ExecutionResult.simulated`), not just in the UI, so nothing can quietly
  pretend a mock action was real.
- The recovery-probability model is a hand-tuned, explainable scoring
  function, not a black box — see the TODO in `risk_predictor.py` for
  where a trained model would slot in.
