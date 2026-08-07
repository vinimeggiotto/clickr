"""Gera assets/icon.png e assets/icon.ico a partir do visual do clickr_icon.svg."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"


def transform(x: float, y: float) -> tuple[float, float]:
    # g transform="translate(74,66) scale(1.3)" no SVG
    return 74 + x * 1.3, 66 + y * 1.3


PATH_PTS = [(20, 15), (20, 78), (36, 63), (47, 85), (58, 79), (47, 57), (68, 57)]
CURSOR = [transform(x, y) for x, y in PATH_PTS]
RING_CX, RING_CY = transform(20, 15)


def make_icon(size: int) -> Image.Image:
    scale = size / 200.0
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    radius = max(4, int(44 * scale))
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(23, 18, 12, 255))
    pad = int(6 * scale)
    d.ellipse([pad, pad, size // 2 + pad, size // 2 + pad], fill=(44, 35, 24, 90))

    cx, cy = RING_CX * scale, RING_CY * scale
    amber = (242, 163, 59, 255)
    amber_dim = (242, 163, 59, 40)
    amber_mid = (242, 163, 59, 77)

    def draw_arc_ring(r: float, width: int, fill: tuple[int, int, int, int]) -> None:
        bbox = [cx - r, cy - r, cx + r, cy + r]
        d.arc(bbox, start=200, end=320, fill=fill, width=max(1, width))

    draw_arc_ring(48 * 1.3 * scale, max(1, int(4 * scale)), amber_dim)
    draw_arc_ring(34 * 1.3 * scale, max(1, int(5 * scale)), amber_mid)

    poly = [(x * scale, y * scale) for x, y in CURSOR]
    d.polygon(poly, fill=amber)
    d.rounded_rectangle(
        [0, 0, size - 1, size - 1],
        radius=radius,
        outline=(255, 255, 255, 15),
        width=max(1, int(scale)),
    )
    return im


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    icon64 = make_icon(64)
    icon64.save(OUT / "icon.png", format="PNG")

    sizes = [16, 32, 48, 64, 128, 256]
    images = [make_icon(s) for s in sizes]
    # Pillow: primeiro frame define; append_images para demais tamanhos
    images[0].save(
        OUT / "icon.ico",
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[1:],
    )
    print(f"OK: {OUT / 'icon.png'}")
    print(f"OK: {OUT / 'icon.ico'}")


if __name__ == "__main__":
    main()
