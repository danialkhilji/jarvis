from pathlib import Path
import config

SKILL_NAME = "remove_background"
SKILL_DESCRIPTION = (
    "Remove the background from a PNG or JPG image using AI. "
    "Saves the result as a PNG with transparent background. "
    "Returns the path to the output file."
)


def run(image_path: str, output_path: str = "") -> str:
    """
    Remove background from an image.

    Args:
        image_path: Absolute path to the source image (JPG or PNG).
        output_path: Optional absolute path for the output PNG.
                     If empty, saves next to the original with '_nobg' suffix.
    """
    try:
        from rembg import remove
        from PIL import Image
    except ImportError:
        return "Error: rembg is not installed. Run: pip install rembg"

    src = Path(image_path)
    if not src.exists():
        return f"Error: File not found: {image_path}"
    if src.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        return f"Error: Unsupported format '{src.suffix}'. Use JPG or PNG."

    allowed = any(str(src).startswith(d) for d in config.ALLOWED_DIRECTORIES)
    if not allowed:
        return f"Error: Access denied. Path must be under an allowed directory."

    dest = Path(output_path) if output_path else src.with_name(src.stem + "_nobg.png")

    with open(src, "rb") as f:
        result = remove(f.read())
    with open(dest, "wb") as f:
        f.write(result)

    return f"Background removed. Saved to: {dest}"
