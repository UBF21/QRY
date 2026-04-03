# Release 0.2.0

## Highlights
- Added strict `order_by` validation with `FilterConfig.reject_invalid_ordering_fields`, so callers can fail fast when ordering fields fall outside the allowlist.
- Introduced `qry.core.validation` plus shared utilities so `CoreFilter` and adapters reuse the same validation logic before translating filters to SQL.
- Built an operator registry (`qry.core.operator_registry`) and example `regex` operator, enabling custom handlers without touching the dispatcher.
- Documented the new extension points and updated the changelog; updated tests and release checklist.

## Testing
- `python3 -m pytest`
