import io

import pytest
import numpy as np
from PIL import Image

from analysis.image_features import analyze_image, sniff_format


def image_bytes(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def solid(color, size=(1080, 1080)):
    return Image.new("RGB", size, color)


def checkerboard(size=1080, square=20):
    tile = np.indices((size, size)).sum(axis=0) // square % 2 * 255
    return Image.fromarray(np.stack([tile] * 3, axis=-1).astype(np.uint8))


def test_sniff_format_by_magic_bytes():
    assert sniff_format(image_bytes(solid((255, 0, 0)))) == "image/png"
    assert sniff_format(image_bytes(solid((255, 0, 0)), fmt="JPEG")) == "image/jpeg"
    assert sniff_format(b"not an image at all") is None


def test_rejects_unknown_format():
    with pytest.raises(ValueError, match="Unrecognized image format"):
        analyze_image(b"garbage bytes here")


def test_solid_image_is_flat_and_flagged():
    m = analyze_image(image_bytes(solid((128, 128, 128))))
    assert m["edge_density"] == 0
    assert m["contrast"] < 1
    assert m["sharpness"] < 1
    assert any("blurry" in f.lower() for f in m["flags"])
    assert any("contrast" in f.lower() for f in m["flags"])


def test_checkerboard_is_sharp_and_busy():
    m = analyze_image(image_bytes(checkerboard()))
    assert m["sharpness"] > 1000
    assert m["edge_density"] > 0.05
    assert m["contrast"] > 100


def test_colorfulness_orders_correctly():
    gray = analyze_image(image_bytes(solid((128, 128, 128))))
    red = analyze_image(image_bytes(solid((255, 0, 0))))
    assert red["colorfulness"] > gray["colorfulness"]


def test_platform_matching():
    square = analyze_image(image_bytes(solid((0, 100, 200), size=(1080, 1080))))
    assert square["nearest_platform"] == "Meta feed (1:1)"
    assert square["aspect_deviation_pct"] == 0

    story = analyze_image(image_bytes(solid((0, 100, 200), size=(1080, 1920))))
    assert "9:16" in story["nearest_platform"]


def test_small_image_is_flagged():
    m = analyze_image(image_bytes(solid((0, 100, 200), size=(300, 300))))
    assert any("600px" in f for f in m["flags"])


def test_brightness_flags():
    dark = analyze_image(image_bytes(solid((10, 10, 10))))
    assert any("dark" in f.lower() for f in dark["flags"])

    bright = analyze_image(image_bytes(solid((250, 250, 250))))
    assert any("bright" in f.lower() for f in bright["flags"])
