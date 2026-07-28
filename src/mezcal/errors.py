from __future__ import annotations


class MezcalError(Exception):
    """Base de todos los errores públicos de Mezcal."""

    code = "mezcal_error"
    http_status = 500


class InvalidQueryError(MezcalError):
    code = "invalid_query"
    http_status = 422


class TransferNotFoundError(MezcalError):
    code = "transfer_not_found"
    http_status = 404


class CEPNotAvailableError(MezcalError):
    code = "cep_not_available"
    http_status = 409


class RateLimitError(MezcalError):
    code = "upstream_rate_limit"
    http_status = 429


class UpstreamError(MezcalError):
    code = "upstream_error"
    http_status = 502


class ParseError(MezcalError):
    code = "parse_error"
    http_status = 502
