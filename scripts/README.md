# FoodInsight Training Datasets

This directory contains tools for preparing and training food detection models.

## Available Datasets

### UEC FOOD 100
- **Location:** `UECFOOD100/`
- **Classes:** 100 Japanese food categories
- **Images:** ~14,000
- **License:** Non-commercial research only

### UEC FOOD 256 (Optional)
- **Location:** `UECFOOD256/`
- **Classes:** 256 food categories (Japanese + international)
- **Images:** ~31,000
- **License:** Non-commercial research only

## Quick Start

### 1. Convert Dataset to YOLO Format

```bash
# Activate virtual environment
cd /Users/bcheung/dev/FoodInsight
source .venv/bin/activate

# Convert UECFOOD100
python datasets/convert_uec_to_yolo.py datasets/UECFOOD100 --output datasets/UECFOOD100_yolo

# Or convert UECFOOD256
python datasets/convert_uec_to_yolo.py datasets/UECFOOD256 --output datasets/UECFOOD256_yolo
```

### 2. Train the Model

```bash
# Train on UECFOOD100 (faster, 100 classes)
python datasets/train.py --data datasets/UECFOOD100_yolo/data.yaml --epochs 100 --device mps

# Train on UECFOOD256 (more classes, longer training)
python datasets/train.py --data datasets/UECFOOD256_yolo/data.yaml --epochs 100 --model yolo11s.pt --device mps

# Use GPU if available
python datasets/train.py --data datasets/UECFOOD100_yolo/data.yaml --device 0
```

**Device options:**
- `0` - CUDA GPU (NVIDIA)
- `mps` - Apple Silicon GPU (Mac M1/M2/M3)
- `cpu` - CPU only (slow)

### 3. Validate the Model

```bash
python datasets/train.py --validate runs/detect/train/weights/best.pt --data datasets/UECFOOD100_yolo/data.yaml
```

### 4. Export for Edge Deployment

```bash
# Export to NCNN (for Raspberry Pi / CPU inference)
python datasets/train.py --export runs/detect/train/weights/best.pt --format ncnn

# Export to ONNX
python datasets/train.py --export runs/detect/train/weights/best.pt --format onnx
```

## Training Tips

### Model Selection
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| yolo11n.pt | 6MB | Fastest | Good | Raspberry Pi, real-time |
| yolo11s.pt | 22MB | Fast | Better | Edge devices with more power |
| yolo11m.pt | 68MB | Medium | Best | Cloud/GPU inference |

### Recommended Settings

**For Raspberry Pi deployment:**
```bash
python datasets/train.py \
    --data datasets/UECFOOD100_yolo/data.yaml \
    --model yolo11n.pt \
    --epochs 100 \
    --imgsz 640 \
    --batch 16
```

**For best accuracy:**
```bash
python datasets/train.py \
    --data datasets/UECFOOD256_yolo/data.yaml \
    --model yolo11s.pt \
    --epochs 150 \
    --imgsz 640 \
    --batch 32 \
    --patience 30
```

## Output Structure

After conversion:
```
UECFOOD100_yolo/
├── data.yaml           # YOLO config file
├── images/
│   ├── train/          # Training images (80%)
│   ├── val/            # Validation images (10%)
│   └── test/           # Test images (10%)
└── labels/
    ├── train/          # Training labels
    ├── val/            # Validation labels
    └── test/           # Test labels
```

After training:
```
runs/detect/train/
├── weights/
│   ├── best.pt         # Best model weights
│   └── last.pt         # Last checkpoint
├── results.csv         # Training metrics
├── confusion_matrix.png
└── ...                 # Other plots
```

## References

- [UEC FOOD 100](http://foodcam.mobi/dataset100.html)
- [UEC FOOD 256](http://foodcam.mobi/dataset256.html)
- [Ultralytics YOLO11](https://docs.ultralytics.com/)
