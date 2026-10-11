"""Декораторы проекта."""

import inspect
import logging

log = logging.getLogger(__name__)


def log_action(func=None, *, verbose=False):
    """Логирует доменные операции по ТЗ 3.4. """

    def decorator(f):
        sig = inspect.signature(f)

        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            action = f.__name__.upper()
            user = bound.arguments.get("user")
            username = (
                getattr(user, "username", None)
                or bound.arguments.get("username")
                or getattr(user, "user_id", None)
            )
            currency = bound.arguments.get("currency")
            amount = bound.arguments.get("amount")

            try:
                result = f(*args, **kwargs)
                rate = result.get("rate") if isinstance(result, dict) else None
                base = bound.arguments.get("base", "USD")
                log.info(
                    "%s user=%r currency=%r amount=%r rate=%r base=%r result=OK",
                    action, username, currency, amount, rate, base,
                )
                if verbose and isinstance(result, dict):
                    log.info(
                        "%s verbose: before=%r after=%r",
                        action, result.get("before"), result.get("after"),
                    )
                return result
            except Exception as e:
                log.error(
                    "%s user=%r currency=%r amount=%r result=ERROR "
                    "error_type=%s error_message=%s",
                    action, username, currency, amount, type(e).__name__, e,
                )
                raise

        return wrapper

    if func is None:
        return decorator
    return decorator(func)