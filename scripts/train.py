#!/usr/bin/env python3
"""Training pipeline for FoodInsight YOLO model.

Fine-tunes YOLO11 on UEC FOOD dataset for food detection.

Usage:
    # Train on UECFOOD100
    python train.py --data UECFOOD100_yolo/data.yaml --epochs 100

    # Train on UECFOOD256
    python train.py --data UECFOOD256_yolo/data.yaml --epochs 100 --model yolo11s.pt

    # Resume training
    python train.py --data UECFOOD100_yolo/data.yaml --resume runs/detect/train/weights/last.pt

    # Export trained model to NCNN (for Raspberry Pi)
    python train.py --export runs/detect/train/weights/best.pt --format ncnn
"""

import argparse
from pathlib import Path


def train(
    data: str,
    model: str = "yolo11n.pt",
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "0",
    patience: int = 20,
    workers: int = 8,
    project: str = "runs/detect",
    name: str = "train",
    resume: str | None = None,
    pretrained: bool = True,
) -> None:
    """Train YOLO model on food dataset.

    Args:
        data: Path to data.yaml
        model: Base model to fine-tune (yolo11n.pt, yolo11s.pt, etc.)
        epochs: Number of training epochs
        imgsz: Input image size
        batch: Batch size (-1 for auto)
        device: CUDA device (0, 1, cpu, or mps for Mac)
        patience: Early stopping patience
        workers: Number of data loader workers
        project: Project directory for outputs
        name: Run name
        resume: Path to checkpoint to resume from
        pretrained: Use pretrained weights for transfer learning
    """
    from ultralytics import YOLO

    # Load model and train
    if resume:
        # Resume from checkpoint - uses saved args.yaml automatically
        print(f"Resuming from: {resume}")
        model_obj = YOLO(resume)
        results = model_obj.train(resume=True)
    else:
        # Fresh training with specified parameters
        print(f"Loading base model: {model}")
        model_obj = YOLO(model)

        print(f"\nStarting training...")
        print(f"  Dataset: {data}")
        print(f"  Epochs: {epochs}")
        print(f"  Image size: {imgsz}")
        print(f"  Batch size: {batch}")
        print(f"  Device: {device}")
        print()

        results = model_obj.train(
            data=data,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            patience=patience,
            workers=workers,
            project=project,
            name=name,
            pretrained=pretrained,
            # Data augmentation (good defaults for food)
            augment=True,
            hsv_h=0.015,  # Hue augmentation
            hsv_s=0.7,    # Saturation augmentation
            hsv_v=0.4,    # Value augmentation
            degrees=10,   # Rotation
            translate=0.1,
            scale=0.5,
            fliplr=0.5,   # Horizontal flip
            flipud=0.0,   # No vertical flip (food orientation matters)
            mosaic=1.0,   # Mosaic augmentation
            mixup=0.1,    # Mixup augmentation
            # Training parameters
            lr0=0.01,     # Initial learning rate
            lrf=0.01,     # Final learning rate factor
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3,
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,
            # Saving
            save=True,
            save_period=-1,  # Save every epoch if > 0
            val=True,
            plots=True,
        )

    print(f"\nTraining complete!")
    print(f"Best weights: {project}/{name}/weights/best.pt")
    print(f"Last weights: {project}/{name}/weights/last.pt")

    return results


def validate(
    model: str,
    data: str,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "0",
) -> None:
    """Validate trained model on test set.

    Args:
        model: Path to trained model weights
        data: Path to data.yaml
        imgsz: Input image size
        batch: Batch size
        device: CUDA device
    """
    from ultralytics import YOLO

    print(f"Validating model: {model}")
    model_obj = YOLO(model)

    results = model_obj.val(
        data=data,
        imgsz=imgsz,
        batch=batch,
        device=device,
        split="test",
    )

    print(f"\nValidation results:")
    print(f"  mAP50: {results.box.map50:.4f}")
    print(f"  mAP50-95: {results.box.map:.4f}")

    return results


def export_model(
    model: str,
    format: str = "ncnn",
    imgsz: int = 640,
    half: bool = False,
    simplify: bool = True,
) -> None:
    """Export trained model to deployment format.

    Args:
        model: Path to trained model weights
        format: Export format (ncnn, onnx, openvino, tflite, etc.)
        imgsz: Input image size
        half: FP16 quantization
        simplify: Simplify ONNX model
    """
    from ultralytics import YOLO

    print(f"Exporting model: {model}")
    print(f"  Format: {format}")
    print(f"  Image size: {imgsz}")
    print(f"  Half precision: {half}")

    model_obj = YOLO(model)

    export_path = model_obj.export(
        format=format,
        imgsz=imgsz,
        half=half,
        simplify=simplify,
    )

    print(f"\nExport complete: {export_path}")

    return export_path


def main():
    parser = argparse.ArgumentParser(description="FoodInsight YOLO Training Pipeline")

    # Mode selection
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export model instead of training (provide model path)",
    )
    parser.add_argument(
        "--validate",
        type=str,
        default=None,
        help="Validate model instead of training (provide model path)",
    )

    # Data
    parser.add_argument(
        "--data", "-d",
        type=str,
        default="UECFOOD100_yolo/data.yaml",
        help="Path to data.yaml",
    )

    # Model
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="yolo11n.pt",
        help="Base model (yolo11n.pt, yolo11s.pt, yolo11m.pt)",
    )
    parser.add_argument(
        "--resume", "-r",
        type=str,
        default=None,
        help="Resume training from checkpoint",
    )

    # Training parameters
    parser.add_argument("--epochs", "-e", type=int, default=100, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--batch", "-b", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="0", help="Device (0, cpu, mps)")
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience")
    parser.add_argument("--workers", type=int, default=8, help="Data loader workers")

    # Output
    parser.add_argument("--project", type=str, default="runs/detect", help="Project dir")
    parser.add_argument("--name", type=str, default="train", help="Run name")

    # Export options
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="ncnn",
        help="Export format (ncnn, onnx, openvino, tflite)",
    )
    parser.add_argument("--half", action="store_true", help="FP16 export")

    args = parser.parse_args()

    # Change to script directory for relative paths
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)

    if args.export:
        # Export mode
        export_model(
            model=args.export,
            format=args.format,
            imgsz=args.imgsz,
            half=args.half,
        )
    elif args.validate:
        # Validation mode
        validate(
            model=args.validate,
            data=args.data,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
        )
    else:
        # Training mode
        train(
            data=args.data,
            model=args.model,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            patience=args.patience,
            workers=args.workers,
            project=args.project,
            name=args.name,
            resume=args.resume,
        )


if __name__ == "__main__":
    main()
