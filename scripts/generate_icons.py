from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw

ICON_SIZES: tuple[int, ...] = (16, 24, 32, 48, 256)
BLUE = (37, 99, 235, 255)
STROKE_WIDTH = 34.0
SUPERSAMPLE = 6
T_PATHS: tuple[str, ...] = (
    "M56 52 L200 52",
    "M128 52 L128 216",
)


def _tokenize_path(path_data: str) -> list[str]:
    return re.findall(r"[MLC]|-?\d+(?:\.\d+)?", path_data)


def _sample_svg_path(path_data: str) -> list[tuple[float, float]]:
    tokens = _tokenize_path(path_data)
    i = 0
    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    while i < len(tokens):
        cmd = tokens[i]
        i += 1
        if cmd == "M":
            current = (float(tokens[i]), float(tokens[i + 1]))
            i += 2
            points.append(current)
            continue
        if cmd == "L":
            current = (float(tokens[i]), float(tokens[i + 1]))
            i += 2
            points.append(current)
            continue
        raise ValueError(f"Unsupported path command: {cmd}")
    return points


def _scale(points: list[tuple[float, float]], size: int) -> list[tuple[int, int]]:
    factor = (size * SUPERSAMPLE) / 256
    return [(round(x * factor), round(y * factor)) for x, y in points]


def _draw_tasker_t(size: int) -> Image.Image:
    hi_size = size * SUPERSAMPLE
    image = Image.new("RGBA", (hi_size, hi_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    width = max(2 * SUPERSAMPLE, round(STROKE_WIDTH * size * SUPERSAMPLE / 256))
    for path_data in T_PATHS:
        draw.line(_scale(_sample_svg_path(path_data), size), fill=BLUE, width=width, joint="curve")
    return image.resize((size, size), resample=Image.Resampling.LANCZOS)


def generate_icon_assets(root: Path) -> list[Path]:
    icon_dir = root / "assets" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    images: list[Image.Image] = []
    for size in ICON_SIZES:
        image = _draw_tasker_t(size)
        path = icon_dir / f"tasker-{size}.png"
        image.save(path)
        outputs.append(path)
        images.append(image)
    ico_path = icon_dir / "tasker.ico"
    images[-1].save(ico_path, format="ICO", sizes=[(size, size) for size in ICON_SIZES])
    outputs.append(ico_path)
    return outputs


if __name__ == "__main__":
    for generated in generate_icon_assets(Path(__file__).resolve().parents[1]):
        print(generated)
