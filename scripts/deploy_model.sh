#!/bin/bash
# Deploy trained model for device detection
# Usage: ./scripts/deploy_model.sh [model_path] [output_name]
#
# Examples:
#   ./scripts/deploy_model.sh                                    # Uses default best.pt
#   ./scripts/deploy_model.sh datasets/runs/detect/train/weights/best.pt uecfood100

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Default paths
MODEL_PATH="${1:-datasets/runs/detect/train/weights/best.pt}"
OUTPUT_NAME="${2:-custom_food}"

echo "============================================="
echo "FoodInsight Model Deployment"
echo "============================================="
echo "Model: $MODEL_PATH"
echo "Output name: ${OUTPUT_NAME}_ncnn_model"
echo ""

# Check model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model not found at $MODEL_PATH"
    echo ""
    echo "Available models:"
    find datasets/runs -name "*.pt" 2>/dev/null || echo "  No trained models found"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Step 1: Export to NCNN
echo "[1/3] Exporting model to NCNN format..."
cd datasets
python train.py --export "../$MODEL_PATH" --format ncnn
cd "$PROJECT_ROOT"

# Get the exported model directory (same location as .pt but with _ncnn_model suffix)
EXPORTED_DIR="${MODEL_PATH%.pt}_ncnn_model"

if [ ! -d "$EXPORTED_DIR" ]; then
    echo "Error: Export failed - $EXPORTED_DIR not found"
    exit 1
fi

# Step 2: Copy to models directory
echo ""
echo "[2/3] Copying to models directory..."
mkdir -p models
DEST_DIR="models/${OUTPUT_NAME}_ncnn_model"

if [ -d "$DEST_DIR" ]; then
    echo "  Removing existing $DEST_DIR"
    rm -rf "$DEST_DIR"
fi

cp -r "$EXPORTED_DIR" "$DEST_DIR"
echo "  Copied to: $DEST_DIR"

# Step 3: Update config
echo ""
echo "[3/3] Model ready for deployment!"
echo ""
echo "============================================="
echo "Deployment Complete"
echo "============================================="
echo ""
echo "Model location: $DEST_DIR"
echo ""
echo "To use with detection service:"
echo ""
echo "  # Update your config file model_path:"
echo "  \"model_path\": \"$PROJECT_ROOT/$DEST_DIR\""
echo ""
echo "  # Or run with UECFOOD100 config:"
echo "  python run_dev.py --config uecfood100_config.json"
echo ""
echo "  # Or start all services:"
echo "  ./scripts/start-dev.sh --config uecfood100_config.json"
echo ""
