#!/usr/bin/env python3
"""Create an asymmetric collage of detected hot dog images."""

from pathlib import Path
from PIL import Image

# Selected diverse hot dog images with good detection scores
IMAGES = [
    # Top row: 2 images
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD100_label_detected/097_hot_dog/13495.jpg",  # ketchup, mustard 0.93
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD100_label_detected/097_hot_dog/13500.jpg",  # lettuce wrap 0.92
    # Bottom row: 2 images
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD100_label_detected/097_hot_dog/13508.jpg",  # with fries 0.72
    "/Users/bcheung/dev/FoodInsight/datasets/UECFOOD100_label_detected/097_hot_dog/13496.jpg",  # mustard 0.92
]


def create_asymmetric_collage(
    image_paths: list[str],
    output_path: str,
    total_width: int = 700,
    gap: int = 3,
):
    """Create a 2x2 asymmetric grid collage."""
    # Load all images
    images = [Image.open(p) for p in image_paths]

    # Calculate cell dimensions for 2x2 grid
    cell_width = (total_width - gap) // 2
    cell_height = int(cell_width * 0.75)  # 4:3 aspect ratio

    total_height = cell_height * 2 + gap

    # Create canvas
    collage = Image.new("RGB", (total_width, total_height), (255, 255, 255))

    positions = [
        (0, 0),                          # Top-left
        (cell_width + gap, 0),           # Top-right
        (0, cell_height + gap),          # Bottom-left
        (cell_width + gap, cell_height + gap),  # Bottom-right
    ]

    for img, (x, y) in zip(images, positions):
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

        # Paste into collage
        collage.paste(img, (x, y))

    # Save collage
    collage.save(output_path, quality=95)
    print(f"Collage saved to: {output_path}")
    print(f"Dimensions: {total_width}x{total_height}")
    return collage


if __name__ == "__main__":
    output_dir = Path("/Users/bcheung/dev/FoodInsight/datasets")
    output_path = output_dir / "hot_dog_detection_collage.jpg"

    create_asymmetric_collage(IMAGES, str(output_path))
