"""Static location dimensions for weekly reporting aggregates."""

from __future__ import annotations

# Trailing baseline window for price-alert derivation (ISO weeks before target week).
PRICE_ALERT_BASELINE_WEEKS: int = 4

# Flag a supply order when unit_cost deviates from the median baseline by more than this percent.
PRICE_ALERT_THRESHOLD_PCT: float = 25.0

# Underscore slugs must match uis/backoffice/lib/locations.ts LOCATION_MAP values.
# Never mix COP and USD in a single aggregate row.
LOCATION_DIMENSIONS: dict[str, tuple[str, str]] = {
    "medellin_centro": ("CO", "COP"),
    "medellin_poblado": ("CO", "COP"),
    "medellin_laureles": ("CO", "COP"),
    "bogota_zona_rosa": ("CO", "COP"),
    "bogota_chapinero": ("CO", "COP"),
    "bogota_usaquen": ("CO", "COP"),
    "bogota_norte": ("CO", "COP"),
    "cali_san_fernando": ("CO", "COP"),
    "cali_granada": ("CO", "COP"),
    "cali_ciudad_jardin": ("CO", "COP"),
    "miami_brickell": ("US", "USD"),
    "miami_wynwood": ("US", "USD"),
    "miami_coral_gables": ("US", "USD"),
    "miami_kendall": ("US", "USD"),
}
