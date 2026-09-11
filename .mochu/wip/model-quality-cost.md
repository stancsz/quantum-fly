# model-quality-cost: bounded quality and cost measurement

Goal: establish a repeatable measurement surface before making any model quality or cost advantage claim.

Decisions:
- Measure a fixed prompt, fixed model, and fixed output budget against an explicit expected answer so quality and usage are observable.
- Keep this as a WIP milestone; repeated measurement is not evidence of superiority without a predeclared independent baseline.

Milestones:
- [x] M1 Run a bounded repeated live measurement with response quality, latency, usage, cost, errors, and resources — verifier: model-quality-cost-surface — shipped iter-4
- [ ] M2 Compare against an independently selected baseline across repeated tasks and report uncertainty — verifier: model-quality-cost-baseline

Current: M2 blocked on baseline availability. Evidence: `outputs/model-quality-cost-baseline.json` has candidate 3/3 success and `gpt-6-astra` baseline 2/3 with one HTTP 503. Next action: resolve the INBOX baseline decision, then rerun the same frozen matched-task verifier.
