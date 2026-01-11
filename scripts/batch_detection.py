#!/usr/bin/env python3
"""Batch detection script for YOLO11 NCNN model.

Walks a directory of images and runs detection on each, saving annotated results.

Usage:
    python scripts/batch_detection.py <input_dir> [output_dir]
    python scripts/batch_detection.py /path/to/images --output /path/to/results
    python scripts/batch_detection.py /path/to/images --confidence 0.3 --no-save
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


def draw_detections(
    image: np.ndarray,
    results,
    font_scale: float = 0.6,
    thickness: int = 2,
) -> np.ndarray:
    """Draw bounding boxes and labels on image."""
    annotated = image.copy()

    if results.boxes is None or len(results.boxes) == 0:
        return annotated

    colors = {}

    for box in results.boxes:
        class_id = int(box.cls)
        class_name = results.names[class_id]
        confidence = float(box.conf)
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        if class_id not in colors:
            np.random.seed(class_id)
            colors[class_id] = tuple(map(int, np.random.randint(0, 255, 3)))
        color = colors[class_id]

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        label = f"{class_name}: {confidence:.2f}"
        (label_w, label_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )

        cv2.rectangle(
            annotated,
            (x1, y1 - label_h - baseline - 5),
            (x1 + label_w, y1),
            color,
            -1,
        )

        cv2.putText(
            annotated,
            label,
            (x1, y1 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
        )

    return annotated


def find_images(input_dir: Path) -> list[Path]:
    """Find all image files in directory recursively."""
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = []
    for ext in extensions:
        images.extend(input_dir.rglob(f"*{ext}"))
        images.extend(input_dir.rglob(f"*{ext.upper()}"))
    return sorted(set(images))


def main():
    parser = argparse.ArgumentParser(
        description="Batch detection on a directory of images"
    )
    parser.add_argument("input_dir", help="Input directory containing images")
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for annotated images (default: <input>_detected)",
    )
    parser.add_argument(
        "--model",
        default="/Users/bcheung/dev/FoodInsight/models/uecfood100_ncnn_model",
        help="Path to NCNN model directory",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.4,
        help="Confidence threshold (default: 0.4)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=640,
        help="Input size for inference (default: 640)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save annotated images, only generate CSV report",
    )
    parser.add_argument(
        "--csv",
        help="Path to save CSV report (default: <output>/detections.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of images to process (for testing)",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)

    # Set output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = input_dir.parent / f"{input_dir.name}_detected"

    if not args.no_save:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {output_dir}")

    # CSV report path
    csv_path = Path(args.csv) if args.csv else output_dir / "detections.csv"

    # Find images
    print(f"Scanning {input_dir} for images...")
    images = find_images(input_dir)
    total_images = len(images)

    if args.limit:
        images = images[: args.limit]
        print(f"Found {total_images} images, processing first {args.limit}")
    else:
        print(f"Found {total_images} images")

    if not images:
        print("No images found!")
        sys.exit(1)

    # Load model
    print(f"Loading model from: {args.model}")
    model = YOLO(args.model)

    # Warm up
    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
    model.predict(dummy, conf=args.confidence, imgsz=args.size, verbose=False)
    print("Model loaded and warmed up")

    # Process images
    print(f"\nProcessing images (confidence={args.confidence})...")
    print("-" * 60)

    results_data = []
    start_time = time.time()
    images_with_detections = 0
    total_detections = 0

    for i, img_path in enumerate(images):
        # Read image
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  Warning: Could not read {img_path}")
            continue

        # Run inference
        results = model.predict(
            image,
            conf=args.confidence,
            imgsz=args.size,
            verbose=False,
        )
        result = results[0]

        # Count detections
        num_detections = len(result.boxes) if result.boxes is not None else 0
        if num_detections > 0:
            images_with_detections += 1
            total_detections += num_detections

        # Record detections
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls)
                class_name = result.names[class_id]
                confidence = float(box.conf)
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                # Relative path for CSV
                rel_path = img_path.relative_to(input_dir)

                results_data.append({
                    "image": str(rel_path),
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                })

        # Save annotated image
        if not args.no_save and num_detections > 0:
            annotated = draw_detections(image, result)
            rel_path = img_path.relative_to(input_dir)
            out_path = output_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), annotated)

        # Progress
        if (i + 1) % 100 == 0 or (i + 1) == len(images):
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (len(images) - i - 1) / rate if rate > 0 else 0
            print(
                f"  [{i+1:>5}/{len(images)}] "
                f"{rate:.1f} img/s | "
                f"ETA: {eta:.0f}s | "
                f"Detections: {total_detections}"
            )

    elapsed = time.time() - start_time

    # Save CSV report
    if results_data:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["image", "class_id", "class_name", "confidence", "x1", "y1", "x2", "y2"],
            )
            writer.writeheader()
            writer.writerows(results_data)
        print(f"\nCSV report saved to: {csv_path}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total images processed:    {len(images):,}")
    print(f"Images with detections:    {images_with_detections:,} ({images_with_detections/len(images)*100:.1f}%)")
    print(f"Total detections:          {total_detections:,}")
    print(f"Time elapsed:              {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"Average speed:             {len(images)/elapsed:.1f} img/s")
    print(f"Average per image:         {elapsed/len(images)*1000:.1f}ms")

    if not args.no_save:
        print(f"Annotated images saved to: {output_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
