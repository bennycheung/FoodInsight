# FoodInsight Scripts

Helper scripts for development and training workflows.

## Development Scripts

### start-dev.sh

Starts all FoodInsight development services (backend, frontend, detection).

```bash
# Default config (dev_config.json)
./scripts/start-dev.sh

# Custom config file for different models/classes
./scripts/start-dev.sh --config custom_config.json
./scripts/start-dev.sh -c food_config.json

# Override camera index
CAMERA_INDEX=0 ./scripts/start-dev.sh
```

**Services started:**
| Service | Port | Description |
|---------|------|-------------|
| FastAPI Backend | 8000 | API server (SQLite) |
| Vue PWA | 5173 | Consumer inventory view |
| Flask Admin | 8080 | Detection + admin portal |

### stop-dev.sh

Stops all running development services.

```bash
./scripts/stop-dev.sh
```

Kills processes on ports 8000, 5173, and 8080.

## Deployment Scripts

### deploy_model.sh

Exports a trained model to NCNN and prepares it for device deployment.

```bash
# Deploy default best.pt from training
./scripts/deploy_model.sh

# Deploy specific model with custom name
./scripts/deploy_model.sh datasets/runs/detect/train/weights/best.pt uecfood100

# Result: models/uecfood100_ncnn_model/
```

**What it does:**
1. Exports `.pt` model to NCNN format (for Raspberry Pi / CPU inference)
2. Copies exported model to `models/` directory
3. Prints instructions for using with config files

## Training Scripts

### convert_uec_to_yolo.py

Converts UEC FOOD datasets to YOLO format for training.

```bash
# Convert UECFOOD100
python scripts/convert_uec_to_yolo.py datasets/UECFOOD100 --output datasets/UECFOOD100_yolo

# Convert UECFOOD256
python scripts/convert_uec_to_yolo.py datasets/UECFOOD256 --output datasets/UECFOOD256_yolo
```

### train.py

Trains, validates, and exports YOLO models.

```bash
# Train on food dataset
python scripts/train.py --data datasets/UECFOOD100_yolo/data.yaml --epochs 100 --device mps

# Validate trained model
python scripts/train.py --validate runs/detect/train/weights/best.pt --data datasets/UECFOOD100_yolo/data.yaml

# Export to NCNN (for Raspberry Pi)
python scripts/train.py --export runs/detect/train/weights/best.pt --format ncnn
```

**Device options:**
- `0` - CUDA GPU (NVIDIA)
- `mps` - Apple Silicon GPU (Mac M1/M2/M3)
- `cpu` - CPU only (slow)

## Configuration Files

The detection service reads settings from JSON config files. Create different configs for different use cases:

**dev_config.json** (default):
```json
{
  "machine_id": "breakroom-1",
  "model_path": "/path/to/models/yolo11n_ncnn_model",
  "input_size": 640,
  "admin_port": 8080,
  "camera_index": 1,
  "api_url": "http://localhost:8000",
  "allowed_classes": ["bottle", "cup", "banana", "apple", "pizza", "donut"]
}
```

**Config options:**
| Option | Type | Description |
|--------|------|-------------|
| `machine_id` | string | Unique device identifier |
| `model_path` | string | Path to YOLO NCNN model |
| `input_size` | int | Model input size (320, 640) |
| `admin_port` | int | Flask admin portal port |
| `camera_index` | int | OpenCV camera index (0, 1, ...) |
| `api_url` | string | Backend API URL |
| `allowed_classes` | array | Classes to detect (empty = all) |
| `motion_threshold` | float | Motion sensitivity (default: 0.008) |
| `process_every_n_frames` | int | Frame skip for detection (default: 1) |

**Example configs:**
- `dev_config.json` - Default development config
- `food_only_config.json` - Only food classes
- `all_classes_config.json` - All COCO/YOLO classes
- `high_sensitivity_config.json` - Lower motion threshold
