#!/usr/bin/env python3
"""Test detection script for YOLO11 NCNN model.

Usage:
    python scripts/test_detection.py <input_image> [output_image]

Examples:
    python scripts/test_detection.py test.jpg
    python scripts/test_detection.py test.jpg result.jpg
    python scripts/test_detection.py test.jpg --confidence 0.3
"""

import argparse
import sys
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
    """Draw bounding boxes and labels on image.

    Args:
        image: BGR image as numpy array
        results: YOLO prediction results
        font_scale: Font size for labels
        thickness: Line thickness for boxes

    Returns:
        Annotated image
    """
    annotated = image.copy()

    if results.boxes is None or len(results.boxes) == 0:
        cv2.putText(
            annotated,
            "No detections",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2,
        )
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


def main():
    parser = argparse.ArgumentParser(
        description="Test YOLO11 NCNN model on a single image"
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output image path (default: input_detected.jpg)",
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
        "--show",
        action="store_true",
        help="Display result in window (requires display)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_detected{input_path.suffix}"

    print(f"Loading model from: {args.model}")
    model = YOLO(args.model)

    print(f"Reading image: {input_path}")
    image = cv2.imread(str(input_path))
    if image is None:
        print(f"Error: Could not read image: {input_path}")
        sys.exit(1)

    print(f"Running inference (confidence={args.confidence}, size={args.size})...")
    results = model.predict(
        image,
        conf=args.confidence,
        imgsz=args.size,
        verbose=False,
    )

    result = results[0]
    num_detections = len(result.boxes) if result.boxes is not None else 0
    print(f"Found {num_detections} detection(s)")

    if result.boxes is not None:
        for i, box in enumerate(result.boxes):
            class_id = int(box.cls)
            class_name = result.names[class_id]
            confidence = float(box.conf)
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            print(f"  [{i+1}] {class_name}: {confidence:.2%} @ ({x1}, {y1}, {x2}, {y2})")

    annotated = draw_detections(image, result)

    cv2.imwrite(str(output_path), annotated)
    print(f"Saved result to: {output_path}")

    if args.show:
        cv2.imshow("Detection Result", annotated)
        print("Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
