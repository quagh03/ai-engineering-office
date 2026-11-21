"""AI Engineering Office engine."""

from importlib.metadata import PackageNotFoundError, version

_FALLBACK_VERSION = "0.1.0"


def _read_version() -> str:
    try:
        return version("aio")
    except PackageNotFoundError:
        return _FALLBACK_VERSION


__version__ = _read_version()
