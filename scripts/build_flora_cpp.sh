#!/bin/bash
# Build the native FLoRa physical layer library used by the flora_cpp model

set -e

# Navigate to the repository root even if script executed elsewhere
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

FLORA_DIR="$ROOT_DIR/flora-master"

if [ ! -d "$FLORA_DIR" ]; then
    echo "Directory '$FLORA_DIR' not found" >&2
    exit 1
fi

cd "$FLORA_DIR"

# Generate makefiles if missing
if [ ! -f src/Makefile ]; then
    make makefiles
fi

LIB_NAME="libflora_phy.so"
make "$LIB_NAME" -j$(nproc)

LAUNCHER_DIR="$ROOT_DIR/simulateur_lora_sfrd/launcher"
mkdir -p "$LAUNCHER_DIR"
cp "$FLORA_DIR/$LIB_NAME" "$LAUNCHER_DIR/"

echo "Placed library in $LAUNCHER_DIR/$LIB_NAME"
