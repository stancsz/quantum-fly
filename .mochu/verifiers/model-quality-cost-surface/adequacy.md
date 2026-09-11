# Verifier adequacy audit

1. A lazy artifact that writes three static `READY` strings would fail because the verifier executes three real router calls and checks telemetry from each response.
2. A lazy artifact that reports latency but drops provider usage or cost would fail because every attempt must contain usage and cost fields.
3. A lazy artifact that reports a repeated success as an advantage would fail because the receipt must carry an explicit limitation saying that no advantage is established.

The suite executes the live model path, inspects substantive metrics, and preserves the distinction between measurement and superiority.
