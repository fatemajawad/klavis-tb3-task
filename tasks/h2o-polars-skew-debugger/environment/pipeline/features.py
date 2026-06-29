# Shared feature configuration between training and serving

NUMERIC_FEATURES = ["age", "income", "tenure_days", "session_count", "page_views"]
CATEGORICAL_FEATURES = ["plan_type", "country", "device_type"]
TARGET = "churned"

PLAN_TYPES = ["free", "basic", "pro", "enterprise"]
COUNTRIES = ["US", "UK", "CA", "AU", "DE"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
