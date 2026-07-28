"""Mezcal: herramientas abiertas para consultar CEP de Banxico."""

from .client import MezcalClient
from .errors import (
    CEPNotAvailableError,
    InvalidQueryError,
    MezcalError,
    RateLimitError,
    TransferNotFoundError,
    UpstreamError,
)
from .models import Account, CEPQuery, Money, Transfer
from .receipt import CEPReceipt

__all__ = [
    "Account",
    "CEPNotAvailableError",
    "CEPQuery",
    "CEPReceipt",
    "InvalidQueryError",
    "MezcalClient",
    "MezcalError",
    "Money",
    "RateLimitError",
    "Transfer",
    "TransferNotFoundError",
    "UpstreamError",
]

__version__ = "0.1.0"
