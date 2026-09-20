# Agent guidance

- Keep orchestration provider-independent; provider SDKs stay in adapters.
- Treat cost, tokens, latency, retries, and model identity as first-class metrics.
- Support small public websites only; crawl and retry loops must be bounded.
- Never fabricate source facts. Sensitive facts require human verification.
- Use deterministic Python orchestration and objective validators.
- Isolate every job in its workspace and never commit secrets.
- Tests use MockProvider and must not make paid API calls.
- Prefer the smallest maintainable abstraction over speculative infrastructure.
