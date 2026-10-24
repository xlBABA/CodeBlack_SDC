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
Verify platform/frontend budgets before activating a timeout trial or introducing
a total deadline; do not describe phase timeouts as wall-clock bounds.

The user approved local implementation and validation of a bounded read-phase
experiment (30-second default, maximum 40), not activation in any environment.

**Why:** Later production evidence identified ReadTimeout near 30 seconds, but
queue/cold-start/execution telemetry and the platform deadline remain unavailable;
this approval is an experiment, not evidence of a root-cause fix.

**How to apply:** Obtain separate approval before activation, paid probes, commits,
merges, pushes or publishing. For a future approved trial, restore 30 or remove the
override if manual review persists, a browser/platform timeout occurs, or total
duration reaches 50 seconds. Account for cached settings requiring process restart.
