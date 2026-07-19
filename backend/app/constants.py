# Canonical hardware statuses used across the app.
STATUS_AVAILABLE = "Available"
STATUS_IN_USE = "In Use"
STATUS_REPAIR = "Repair"

# Statuses a device can legitimately hold in the dashboard.
VALID_STATUSES = {STATUS_AVAILABLE, STATUS_IN_USE, STATUS_REPAIR}

# Only devices in this status can be rented.
RENTABLE_STATUSES = {STATUS_AVAILABLE}
