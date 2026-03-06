"""
Render all Mermaid diagrams from DIAGRAMS.md into JPEG images.

Usage:
    python render_diagrams.py

Requires:
    - npx @mermaid-js/mermaid-cli  (auto-installed via npx -y)
    - Pillow                        (pip install Pillow)
"""

import os
import re
import subprocess
import sys
import json
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAMS_MD = os.path.join(SCRIPT_DIR, "DIAGRAMS.md")

# Output filenames matching the existing naming convention
DIAGRAM_NAMES = [
    "01_architecture",
    "02_pipeline",
    "03_classes",
    "04_features",
    "05_collection_seq",
    "06_training_seq",
    "07_live_seq",
    "08_state_machine",
    "09_model_arch",
]


def extract_mermaid_blocks(md_path: str) -> list[str]:
    """Extract all ```mermaid ... ``` blocks from a markdown file."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    return re.findall(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)


def png_to_jpg(png_path: str, jpg_path: str, quality: int = 92):
    """Convert PNG to JPEG using Pillow."""
    from PIL import Image
    img = Image.open(png_path).convert("RGB")
    img.save(jpg_path, "JPEG", quality=quality)


def render_diagram(mermaid_src: str, output_jpg: str) -> bool:
    """Render a single Mermaid diagram: mmdc -> PNG -> convert to JPG."""
    # Write mermaid source to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
        f.write(mermaid_src)
        mmd_path = f.name

    # Temp PNG output
    png_path = output_jpg.replace(".jpg", ".png")

    # Write mmdc config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"theme": "default"}, f)
        config_path = f.name

    try:
        result = subprocess.run(
            [
                "npx", "-y", "@mermaid-js/mermaid-cli",
                "-i", mmd_path,
                "-o", png_path,
                "-c", config_path,
                "-s", "3",           # scale factor for crisp output
                "-b", "white",
            ],
            capture_output=True, text=True, timeout=60,
            shell=True,
        )
        if result.returncode != 0:
            print(f"  mmdc ERROR: {result.stderr.strip()}")
            return False

        # Convert PNG -> JPEG
        png_to_jpg(png_path, output_jpg)

        # Clean up intermediate PNG
        if os.path.exists(png_path):
            os.unlink(png_path)

        return True
    except subprocess.TimeoutExpired:
        print("  ERROR: Rendering timed out")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        if os.path.exists(mmd_path):
            os.unlink(mmd_path)
        if os.path.exists(config_path):
            os.unlink(config_path)


def main():
    if not os.path.exists(DIAGRAMS_MD):
        print(f"Not found: {DIAGRAMS_MD}")
        sys.exit(1)

    blocks = extract_mermaid_blocks(DIAGRAMS_MD)
    print(f"Found {len(blocks)} Mermaid blocks in DIAGRAMS.md")

    if len(blocks) != len(DIAGRAM_NAMES):
        print(f"WARNING: Expected {len(DIAGRAM_NAMES)} diagrams, found {len(blocks)}")

    success = 0
    for i, (name, src) in enumerate(zip(DIAGRAM_NAMES, blocks)):
        out = os.path.join(SCRIPT_DIR, f"{name}.jpg")
        print(f"[{i+1}/{len(blocks)}] Rendering {name}.jpg ...")
        if render_diagram(src, out):
            size_kb = os.path.getsize(out) / 1024
            print(f"  OK ({size_kb:.0f} KB)")
            success += 1
        else:
            print(f"  FAILED")

    print(f"\nDone: {success}/{len(blocks)} diagrams rendered")


if __name__ == "__main__":
    main()
