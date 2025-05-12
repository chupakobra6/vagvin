"""
This module is a backward compatibility layer for code that imports PaymentService from accounts.payments.
It simply re-exports the PaymentService from the payments app.
"""

from apps.payments.services import PaymentService 