"""Local computer-vision metrics for ad creatives.

All metrics here are computed from raw pixel arrays with numpy — no ML,
no API. They answer the mechanical questions (is it sharp, is it sized
for the platform, will it survive feed compression?) while Claude vision
handles the semantic ones (is the message any good?).
"""

import io
import numpy as np
from PIL import Image

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ANALYSIS_SIZE = 512  # metrics are computed on a downscaled copy for speed

# Format detection by magic bytes rather than trusting file extensions or
# client-supplied MIME types — the first few bytes of a file identify it.
MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # verified against bytes 8-12 below
]

# Common paid-placement specs. Aspect ratio is width/height.
PLATFORM_SPECS = [
    ("Meta feed (1:1)", 1.0),
    ("Meta feed (4:5)", 0.8),
    ("Stories / Reels / TikTok (9:16)", 9 / 16),
    ("YouTube / landscape (16:9)", 16 / 9),
]


def sniff_format(data):
    """Identify image format from magic bytes. Returns MIME type or None."""
    for signature, mime in MAGIC_SIGNATURES:
        if data.startswith(signature):
            if mime == "image/webp" and data[8:12] != b"WEBP":
                continue
            return mime
    return None


def to_grayscale(rgb):
    """ITU-R BT.601 luma transform — how perceived brightness weights RGB."""
    return rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114


def convolve3x3(gray, kernel):
    """3x3 convolution using shifted views instead of an explicit loop.

    Each kernel cell multiplies a copy of the image shifted by that cell's
    offset; summing the nine shifted products equals sliding the kernel
    across every pixel. Same result as scipy.signal.convolve2d(mode='valid')
    without the scipy dependency.
    """
    h, w = gray.shape
    out = np.zeros((h - 2, w - 2), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            if kernel[i][j] != 0:
                out += kernel[i][j] * gray[i:h - 2 + i, j:w - 2 + j]
    return out


def laplacian_sharpness(gray):
    """Variance of the Laplacian — the standard blur detector.

    The Laplacian responds to intensity changes (edges). A sharp image has
    strong edge responses in both directions, so the variance is high; a
    blurry image's responses cluster near zero.
    """
    kernel = [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    return float(convolve3x3(gray, kernel).var())


def edge_density(gray):
    """Fraction of pixels that sit on a Sobel edge.

    Very low = flat/empty creative; very high = visual noise that reads
    badly at feed size.
    """
    sobel_x = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    sobel_y = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    gx = convolve3x3(gray, sobel_x)
    gy = convolve3x3(gray, sobel_y)
    magnitude = np.sqrt(gx**2 + gy**2)
    return float(np.mean(magnitude > 100))


def colorfulness(rgb):
    """Hasler & Süsstrunk (2003) colorfulness metric.

    Projects RGB onto two opponent axes (red-green, yellow-blue) and
    combines the spread and strength of those signals. Correlates well
    with how 'colorful' humans rate an image. Rough scale: <15 muted,
    15-35 moderate, >35 vivid.
    """
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    rg = r - g
    yb = 0.5 * (r + g) - b
    std_root = np.sqrt(rg.std() ** 2 + yb.std() ** 2)
    mean_root = np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    return float(std_root + 0.3 * mean_root)


def nearest_platform(width, height):
    ratio = width / height
    best_name, best_ratio = min(PLATFORM_SPECS, key=lambda spec: abs(spec[1] - ratio))
    deviation = abs(best_ratio - ratio) / best_ratio
    return best_name, round(deviation * 100, 1)


def analyze_image(data):
    """Run the full local analysis on raw image bytes."""
    mime = sniff_format(data)
    if mime is None:
        raise ValueError("Unrecognized image format — PNG, JPEG, GIF, or WebP only")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds {MAX_IMAGE_BYTES // (1024 * 1024)}MB limit")

    img = Image.open(io.BytesIO(data)).convert("RGB")
    width, height = img.size

    small = img.copy()
    small.thumbnail((ANALYSIS_SIZE, ANALYSIS_SIZE))
    rgb = np.asarray(small, dtype=np.float64)
    gray = to_grayscale(rgb)

    brightness = float(gray.mean())
    contrast = float(gray.std())  # RMS contrast
    sharpness = laplacian_sharpness(gray)
    edges = edge_density(gray)
    color = colorfulness(rgb)
    platform, deviation_pct = nearest_platform(width, height)

    flags = []
    if min(width, height) < 600:
        flags.append(f"{width}x{height} is below the 600px minimum most platforms want")
    if deviation_pct > 5:
        flags.append(f"Aspect ratio is {deviation_pct}% off from {platform} — expect cropping")
    if sharpness < 50:
        flags.append("Image appears blurry (low Laplacian variance)")
    if brightness < 50:
        flags.append("Very dark image — likely to disappear in a bright feed")
    if brightness > 220:
        flags.append("Blown-out bright image — low contrast against white UI")
    if contrast < 25:
        flags.append("Low contrast — text and subject may not separate")
    if edges > 0.25:
        flags.append("Very busy image — unlikely to read clearly at feed size")

    return {
        "format": mime,
        "width": width,
        "height": height,
        "file_size_kb": round(len(data) / 1024, 1),
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "sharpness": round(sharpness, 1),
        "edge_density": round(edges, 3),
        "colorfulness": round(color, 1),
        "nearest_platform": platform,
        "aspect_deviation_pct": deviation_pct,
        "flags": flags,
    }
