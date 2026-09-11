# Verifier adequacy audit

The verifier must execute the documented entry point and inspect the resulting receipt, not merely check that files or prose exist.

1. A lazy artifact that only greps README for the word `quickstart` would pass a presence check but fail here because the verifier runs `python -m scripts.quickstart`.
2. A lazy artifact that creates an empty `outputs/local-research-run.json` would pass an existence check but fail here because the verifier parses required connectome, backtest, resource, and limitation fields.
3. A lazy artifact that runs only the classical happy path and drops provenance would fail here because the verifier requires ID integrity, retained-edge counts, runtime receipt data, and explicit limitations.

The suite therefore executes the user-facing path and validates substance, not only presence.
