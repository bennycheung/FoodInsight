#!/usr/bin/env python3
"""Convert UEC FOOD dataset to YOLO format.

UEC FOOD format:
- Each class has a directory (1-100 or 1-256)
- bb_info.txt contains: img x1 y1 x2 y2 (absolute pixel coords)
- category.txt maps class ID to name

YOLO format:
- images/train/, images/val/, images/test/
- labels/train/, labels/val/, labels/test/
- Each label file: class_id x_center y_center width height (normalized 0-1)
- data.yaml with class names and paths

Usage:
    python convert_uec_to_yolo.py UECFOOD100 --output uec100_yolo
    python convert_uec_to_yolo.py UECFOOD256 --output uec256_yolo
"""

import argparse
import random
import shutil
from pathlib import Path

from PIL import Image


def parse_category_file(category_path: Path) -> dict[int, str]:
    """Parse category.txt to get class ID -> name mapping."""
    categories = {}
    with open(category_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("id"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                class_id = int(parts[0])
                class_name = parts[1].strip()
                # YOLO uses 0-indexed classes
                categories[class_id] = class_name
    return categories


def parse_bb_info(bb_info_path: Path) -> dict[str, tuple[int, int, int, int]]:
    """Parse bb_info.txt to get image -> bbox mapping."""
    bboxes = {}
    with open(bb_info_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("img"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                img_name = parts[0]
                x1, y1, x2, y2 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                bboxes[img_name] = (x1, y1, x2, y2)
    return bboxes


def convert_to_yolo_format(
    bbox: tuple[int, int, int, int],
    img_width: int,
    img_height: int,
) -> tuple[float, float, float, float]:
    """Convert absolute bbox to normalized YOLO format.

    Args:
        bbox: (x1, y1, x2, y2) absolute pixel coordinates
        img_width: Image width in pixels
        img_height: Image height in pixels

    Returns:
        (x_center, y_center, width, height) normalized to 0-1
    """
    x1, y1, x2, y2 = bbox

    # Clamp coordinates to image bounds
    x1 = max(0, min(x1, img_width))
    x2 = max(0, min(x2, img_width))
    y1 = max(0, min(y1, img_height))
    y2 = max(0, min(y2, img_height))

    # Calculate center and dimensions
    x_center = (x1 + x2) / 2.0 / img_width
    y_center = (y1 + y2) / 2.0 / img_height
    width = (x2 - x1) / img_width
    height = (y2 - y1) / img_height

    return x_center, y_center, width, height


def convert_dataset(
    input_dir: Path,
    output_dir: Path,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> None:
    """Convert UEC FOOD dataset to YOLO format.

    Args:
        input_dir: Path to UECFOOD100 or UECFOOD256 directory
        output_dir: Output directory for YOLO format dataset
        train_ratio: Fraction of data for training
        val_ratio: Fraction of data for validation
        test_ratio: Fraction of data for testing
        seed: Random seed for reproducibility
    """
    random.seed(seed)

    # Parse categories
    category_path = input_dir / "category.txt"
    if not category_path.exists():
        raise FileNotFoundError(f"category.txt not found in {input_dir}")

    categories = parse_category_file(category_path)
    num_classes = len(categories)
    print(f"Found {num_classes} classes")

    # Create output directories
    for split in ["train", "val", "test"]:
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    # Collect all samples
    samples = []  # List of (image_path, class_id, bbox)

    for class_id in sorted(categories.keys()):
        class_dir = input_dir / str(class_id)
        if not class_dir.exists():
            print(f"Warning: Class directory {class_id} not found")
            continue

        bb_info_path = class_dir / "bb_info.txt"
        if not bb_info_path.exists():
            print(f"Warning: bb_info.txt not found for class {class_id}")
            continue

        bboxes = parse_bb_info(bb_info_path)

        for img_name, bbox in bboxes.items():
            img_path = class_dir / f"{img_name}.jpg"
            if img_path.exists():
                samples.append((img_path, class_id, bbox))

    print(f"Found {len(samples)} samples")

    # Shuffle and split
    random.shuffle(samples)

    n_total = len(samples)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    splits = {
        "train": samples[:n_train],
        "val": samples[n_train:n_train + n_val],
        "test": samples[n_train + n_val:],
    }

    print(f"Split: train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")

    # Process each split
    processed = 0
    errors = 0

    for split_name, split_samples in splits.items():
        for img_path, class_id, bbox in split_samples:
            try:
                # Get image dimensions
                with Image.open(img_path) as img:
                    img_width, img_height = img.size

                # Convert bbox to YOLO format (0-indexed class)
                yolo_class = class_id - 1  # UEC uses 1-indexed, YOLO uses 0-indexed
                x_center, y_center, width, height = convert_to_yolo_format(
                    bbox, img_width, img_height
                )

                # Skip invalid boxes
                if width <= 0 or height <= 0:
                    errors += 1
                    continue

                # Create unique filename
                unique_name = f"{class_id}_{img_path.stem}"

                # Copy image
                dst_img = output_dir / "images" / split_name / f"{unique_name}.jpg"
                shutil.copy2(img_path, dst_img)

                # Write label file
                dst_label = output_dir / "labels" / split_name / f"{unique_name}.txt"
                with open(dst_label, "w") as f:
                    f.write(f"{yolo_class} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

                processed += 1

            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                errors += 1

    print(f"Processed {processed} images, {errors} errors")

    # Create data.yaml
    yaml_content = f"""# UEC FOOD Dataset converted to YOLO format
# Generated from {input_dir.name}

path: {output_dir.absolute()}
train: images/train
val: images/val
test: images/test

nc: {num_classes}
names:
"""

    # Add class names (0-indexed)
    for class_id in sorted(categories.keys()):
        yaml_content += f"  {class_id - 1}: {categories[class_id]}\n"

    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"Created {yaml_path}")
    print(f"\nConversion complete! Dataset ready at: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Convert UEC FOOD dataset to YOLO format")
    parser.add_argument(
        "input",
        type=str,
        help="Input dataset directory (UECFOOD100 or UECFOOD256)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory (default: {input}_yolo)",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Training set ratio (default: 0.8)",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="Validation set ratio (default: 0.1)",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="Test set ratio (default: 0.1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        # Try relative to script directory
        script_dir = Path(__file__).parent
        input_dir = script_dir / args.input

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {args.input}")

    output_dir = Path(args.output) if args.output else input_dir.parent / f"{input_dir.name}_yolo"

    convert_dataset(
        input_dir=input_dir,
        output_dir=output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
