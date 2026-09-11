# Verifier adequacy audit

1. A lazy artifact that only counts registry rows would pass without executing a single verifier; this suite runs each registered command.
2. A registry containing a missing command would pass a presence check but fails here when subprocess execution returns nonzero.
3. A registry whose quickstart or boundary verifier accepts malformed evidence would fail here because those substantive verifiers are executed as part of the health check.

The suite exercises the verifier corpus rather than asserting that registry text exists.
