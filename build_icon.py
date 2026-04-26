from pathlib import Path

from PIL import Image
from main import create_icon_image


def main():
    icons_dir = Path(__file__).resolve().parent / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    img = create_icon_image(256)
    png_path = icons_dir / "icon.png"
    ico_path = icons_dir / "icon.ico"
    img.save(png_path, format="PNG")
    img.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"icon generated: {png_path}, {ico_path}")


if __name__ == "__main__":
    main()
