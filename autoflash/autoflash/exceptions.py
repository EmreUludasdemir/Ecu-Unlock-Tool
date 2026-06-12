"""AutoFlash hata tipleri."""


class AutoFlashError(Exception):
    """Tum AutoFlash hatalarinin tabani."""


class ConnectionFailed(AutoFlashError):
    """Fiziksel/transport baglantisi kurulamadi."""


class IdentificationError(AutoFlashError):
    """ECU tanimlanamadi veya uygun driver bulunamadi."""


class SecurityAccessError(AutoFlashError):
    """UDS SecurityAccess (0x27) basarisiz - seed/key kabul edilmedi."""


class ChecksumError(AutoFlashError):
    """Checksum dogrulama / duzeltme hatasi."""


class DriverNotFoundError(IdentificationError):
    """Kayitli driver'lar arasinda eslesme yok."""
