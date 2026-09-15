import enum


class UserRole(str, enum.Enum):
    MSP_ADMIN = "msp_admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class SensorStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    OFFLINE = "offline"


class NetworkEventSourceType(str, enum.Enum):
    """Normalized telemetry source identifiers."""

    ZEEK_CONN = "zeek_conn"
