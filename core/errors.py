"""Erros com código estável, traduzíveis pela UI (chaves errors.<code>)."""

from __future__ import annotations

from typing import Any, Optional


class ClickrError(ValueError):
    """Erro de domínio. `code` vira a chave i18n `errors.<code>` na UI."""

    def __init__(self, code: str, message: str = "", **params: Any) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.params = params

    def to_dict(self) -> dict[str, Any]:
        return error_dict(self.code, self.message, **self.params)


def error_dict(code: str, message: str = "", **params: Any) -> dict[str, Any]:
    return {"code": code, "message": message or code, "params": dict(params)}


def error_from_exception(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, ClickrError):
        return exc.to_dict()
    return error_dict("generic", str(exc) or exc.__class__.__name__, detail=str(exc))


def normalize_error(value: Any) -> Optional[dict[str, Any]]:
    """Aceita None, str, dict ou exceção e devolve o formato de erro da UI."""
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, BaseException):
        return error_from_exception(value)
    return error_dict("generic", str(value), detail=str(value))
