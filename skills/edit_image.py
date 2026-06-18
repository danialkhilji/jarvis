from pathlib import Path
import config

SKILL_NAME = "edit_image"
SKILL_DESCRIPTION = (
    "Resize, crop, rotate, or adjust brightness/contrast of an image. "
    "Actions: resize, crop, rotate, brightness, contrast. "
    "Returns the path to the edited image."
)


def run(
    image_path: str,
    action: str,
    output_path: str = "",
    width: int = 0,
    height: int = 0,
    left: int = 0,
    top: int = 0,
    right: int = 0,
    bottom: int = 0,
    degrees: float = 0.0,
    factor: float = 1.0,
) -> str:
    """
    Edit an image.

    Args:
        image_path: Absolute path to the image.
        action: One of 'resize', 'crop', 'rotate', 'brightness', 'contrast'.
        output_path: Optional output path. Defaults to original name with '_edited' suffix.
        width, height: For 'resize' (pixels).
        left, top, right, bottom: For 'crop' (pixel coordinates).
        degrees: For 'rotate'.
        factor: For 'brightness' or 'contrast' — 1.0 is original, 2.0 doubles it.
    """
    try:
        from PIL import Image, ImageEnhance
    except ImportError:
        return "Error: Pillow is not installed. Run: pip install Pillow"

    src = Path(image_path)
    if not src.exists():
        return f"Error: File not found: {image_path}"

    allowed = any(str(src).startswith(d) for d in config.ALLOWED_DIRECTORIES)
    if not allowed:
        return "Error: Access denied. Path must be under an allowed directory."

    valid_actions = ("resize", "crop", "rotate", "brightness", "contrast")
    if action not in valid_actions:
        return f"Error: Unknown action '{action}'. Choose from: {', '.join(valid_actions)}"

    dest = Path(output_path) if output_path else src.with_name(src.stem + "_edited" + src.suffix)

    img = Image.open(src)

    if action == "resize":
        if not width or not height:
            return "Error: 'resize' requires both width and height."
        img = img.resize((width, height), Image.LANCZOS)

    elif action == "crop":
        if not any([left, top, right, bottom]):
            return "Error: 'crop' requires left, top, right, bottom coordinates."
        img = img.crop((left, top, right, bottom))

    elif action == "rotate":
        if not degrees:
            return "Error: 'rotate' requires degrees."
        img = img.rotate(degrees, expand=True)

    elif action == "brightness":
        img = ImageEnhance.Brightness(img).enhance(factor)

    elif action == "contrast":
        img = ImageEnhance.Contrast(img).enhance(factor)

    img.save(dest)
    return f"Image {action} applied. Saved to: {dest}"
