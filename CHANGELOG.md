# Changelog

## [Unreleased]
### Added / Changed
- `FilterConfig.reject_invalid_ordering_fields` lets callers turn on strict `order_by` validation (defaults to `False` to keep prior behavior).
- `parse_order_by_string` and `SQLAlchemyQueryAdapter` now raise `ValueError` when requested ordering columns/directions are invalid, so bad requests fail fast instead of producing bad SQL.
- Documented the new configuration in the README and highlighted the stricter adapter behavior.
- Introduced `qry.core.operator_registry` so handlers can be registered or overridden without modifying the dispatcher, paving the way for more operators.

## [0.1.0] - 2026-04-02
### Added
- core filtering schemas, parsing helpers and public API documentation
- FastAPI `CoreFilter` with relation/having support and SQLAlchemy adapter
- comprehensive tests, CI workflow, formatter and packaging validation
- detailed README usage guide and compatibility notes
