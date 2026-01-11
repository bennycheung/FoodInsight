#!/usr/bin/env python3
"""Create a beautiful food collage from UECFOOD256 images."""

from pathlib import Path
from PIL import Image

# Selected colorful and diverse food images - Set 2
IMAGES = [
    # Row 1: pizza, ramen, tempura, shortcake
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/018_pizza/13829.jpg",
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/023_ramen_noodle/10576.jpg",
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/054_tempura/13750.jpg",
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/120_shortcake/129056.jpg",
    # Row 2: parfait, beef curry, fried chicken, green curry
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/163_parfait/111178.jpg",
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/006_beef_curry/10575.jpg",
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/055_fried_chicken/10638.jpg",
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD256_label/101_green_curry/1164.jpg",
]

def create_collage(
    image_paths: list[str],
    output_path: str,
    cols: int = 4,
    cell_width: int = 175,
    cell_height: int = 130,
    gap: int = 2,
):
    """Create a grid collage from images."""
    rows = (len(image_paths) + cols - 1) // cols

    # Calculate total dimensions
    total_width = cols * cell_width + (cols - 1) * gap
    total_height = rows * cell_height + (rows - 1) * gap

    # Create canvas
    collage = Image.new("RGB", (total_width, total_height), (255, 255, 255))

    for i, img_path in enumerate(image_paths):
        row = i // cols
        col = i % cols

        # Load and resize image
        img = Image.open(img_path)

        # Calculate crop to fill cell while maintaining aspect ratio
        img_ratio = img.width / img.height
        cell_ratio = cell_width / cell_height

        if img_ratio > cell_ratio:
            # Image is wider - crop sides
            new_width = int(img.height * cell_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is taller - crop top/bottom
            new_height = int(img.width / cell_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        # Resize to cell size
        img = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)

        # Calculate position
        x = col * (cell_width + gap)
        y = row * (cell_height + gap)

        # Paste into collage
        collage.paste(img, (x, y))

    # Save collage
    collage.save(output_path, quality=95)
    print(f"Collage saved to: {output_path}")
    print(f"Dimensions: {total_width}x{total_height}")
    return collage


if __name__ == "__main__":
    output_dir = Path("/Users/bcheung/dev/FoodInsight/datasets")
    output_path = output_dir / "UECFOOD256_sample_collage_2.jpg"

    create_collage(IMAGES, str(output_path))
