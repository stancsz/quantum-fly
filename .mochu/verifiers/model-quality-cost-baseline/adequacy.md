# Verifier adequacy audit

1. A lazy artifact with only candidate calls would fail because the verifier requires three successful calls for both candidate and independent baseline arms.
2. A lazy artifact with aggregate quality only would fail because every matched call must carry quality, latency, and usage metrics.
3. A lazy artifact that turns a small sample into an advantage claim would fail because the receipt must include uncertainty and an explicit no-advantage limitation.

The suite requires a real matched comparison and records when provider availability prevents a valid comparison.
