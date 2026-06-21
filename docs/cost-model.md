# Cost model

AgentLens estimates spend when telemetry contains model and token fields.

Pricing is config-driven and lives in `configs/pricing/`.

```yaml
provider: anthropic
currency: USD
models:
  claude-sonnet-4:
    input_per_million_tokens: 3.00
    output_per_million_tokens: 15.00
```

The detector looks for common token fields such as:

- `gen_ai.usage.input_tokens`
- `gen_ai.usage.output_tokens`
- `input_tokens`
- `output_tokens`
- `prompt_tokens`
- `completion_tokens`

Pricing changes frequently. Keep the pricing files current before using these estimates for chargeback or financial reporting.
