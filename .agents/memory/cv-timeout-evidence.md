---
name: CV timeout evidence boundaries
description: Constraints for investigating extraction latency without unsafe timeout guesses
---

Do not increase CV extraction timeouts or run paid provider probes solely because
long Shell requests reportedly succeed.

**Why:** Production timeout logs established the client fallback mechanism but
did not identify the slow phase; the platform's effective upload deadline was
not available in official documentation. Shell prompt/runtime parity was unknown.

**How to apply:** Separate observed failure mechanism from cold-start, network and
payload hypotheses. Require an explicit paid-probe budget and synthetic content.
Verify platform/frontend budgets before introducing a total deadline or tuning
phase limits; do not describe phase timeouts as wall-clock bounds.
