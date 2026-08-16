from enum import Enum


class PaymentProviderName(str, Enum):
    MOCK = "mock"
    STRIPE = "stripe"
    PAYSTACK = "paystack"
    NOWPAYMENTS = "nowpayments"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
