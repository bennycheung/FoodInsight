#!/usr/bin/env python3
"""Rename UECFOOD100 folders to include category names.

Renames folders from "97" to "097_hot_dog" format for better readability.
"""

import argparse
import re
from pathlib import Path


def load_categories(category_file: Path) -> dict[int, str]:
    """Load category mappings from category.txt."""
    categories = {}
    with open(category_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("id"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                cat_id = int(parts[0])
                cat_name = parts[1].strip()
                categories[cat_id] = cat_name
    return categories


def sanitize_name(name: str) -> str:
    """Convert name to filesystem-safe format."""
    # Replace spaces and special chars with underscores
    name = re.sub(r"['\-]", "", name)  # Remove apostrophes and hyphens
    name = re.sub(r"\s+", "_", name)   # Spaces to underscores
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)  # Remove other special chars
    return name.lower()


def main():
    parser = argparse.ArgumentParser(
        description="Rename UECFOOD100 folders to include category names"
    )
    parser.add_argument(
        "--dataset",
        default="/Users/bcheung/dev/FoodInsight/datasets/UECFOOD100",
        help="Path to UECFOOD100 dataset directory",
    )
    parser.add_argument(
        "--categories",
        default="/Users/bcheung/dev/FoodInsight/datasets/UECFOOD100_label/category.txt",
        help="Path to category.txt file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without making changes",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    category_file = Path(args.categories)

    if not dataset_path.exists():
        print(f"Error: Dataset path not found: {dataset_path}")
        return 1

    if not category_file.exists():
        print(f"Error: Category file not found: {category_file}")
        return 1

    categories = load_categories(category_file)
    print(f"Loaded {len(categories)} categories")

    # Find numeric folders
    renamed = 0
    skipped = 0

    for folder in sorted(dataset_path.iterdir()):
        if not folder.is_dir():
            continue

        # Check if folder name is purely numeric
        if not folder.name.isdigit():
            # Already renamed or not a category folder
            skipped += 1
            continue

        folder_id = int(folder.name)
        if folder_id not in categories:
            print(f"Warning: No category found for folder {folder_id}")
            skipped += 1
            continue

        cat_name = categories[folder_id]
        safe_name = sanitize_name(cat_name)
        new_name = f"{folder_id:03d}_{safe_name}"
        new_path = folder.parent / new_name

        if args.dry_run:
            print(f"  {folder.name:>3} -> {new_name} ({cat_name})")
        else:
            folder.rename(new_path)
            print(f"  {folder.name:>3} -> {new_name}")

        renamed += 1

    print(f"\n{'Would rename' if args.dry_run else 'Renamed'}: {renamed} folders")
    if skipped > 0:
        print(f"Skipped: {skipped} items")

    return 0


if __name__ == "__main__":
    exit(main())
