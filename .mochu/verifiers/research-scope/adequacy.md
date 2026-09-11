# Verifier adequacy audit

1. A lazy artifact containing only a heading would fail because all required boundary phrases must be present and the assessment CLI must execute.
2. A lazy artifact that documents limits but breaks the CLI would fail because the verifier invokes the real `scripts.fly_chat` path and requires structured limitations in its output.
3. A lazy artifact that claims "no limitations" would fail because the verifier requires the actual bounded assessment response to expose a `limitations` field.

The suite executes the user-facing assessment path and checks substantive boundary language.
