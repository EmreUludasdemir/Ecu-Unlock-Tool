"""Driver modulleri. Import edildiklerinde kendilerini registry'ye kaydeder."""

from . import mock  # noqa: F401     (sanal ECU ile eslesen test driver'i)
from . import simos18  # noqa: F401  (gercek platform - stub)

__all__ = ["mock", "simos18"]
