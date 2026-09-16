"""Byte-size evidence for delivery JPEG quality levels."""

from __future__ import annotations

import io

from app.core.image_upload import transcode_image_for_delivery
from PIL import Image


def _sample_jpeg_bytes(width: int = 800, height: int = 600) -> bytes:
    image = Image.new("RGB", (width, height), color=(180, 40, 40))
    for x in range(0, width, 40):
        for y in range(0, height, 40):
            image.putpixel((x, y), (x % 255, y % 255, (x + y) % 255))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def test_delivery_quality_50_is_smaller_than_90() -> None:
    source = _sample_jpeg_bytes()
    low, _ = transcode_image_for_delivery(source, jpeg_quality=50)
    high, _ = transcode_image_for_delivery(source, jpeg_quality=90)
    assert len(low) < len(high)
    assert len(low) > 0
    assert len(high) > 0
