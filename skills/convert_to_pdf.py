from pathlib import Path
import config

SKILL_NAME = "convert_to_pdf"
SKILL_DESCRIPTION = (
    "Convert one or more image files (JPG, PNG) to a single PDF. "
    "Pass multiple file paths separated by commas. "
    "Returns the path to the created PDF."
)


def run(input_paths: str, output_path: str = "") -> str:
    """
    Convert images to a PDF.

    Args:
        input_paths: Comma-separated list of absolute file paths (JPG or PNG).
        output_path: Absolute path for the output PDF.
                     If empty, saves next to the first file with '.pdf' extension.
    """
    paths = [Path(p.strip()) for p in input_paths.split(",") if p.strip()]
    if not paths:
        return "Error: No input paths provided."

    for p in paths:
        if not p.exists():
            return f"Error: File not found: {p}"
        allowed = any(str(p).startswith(d) for d in config.ALLOWED_DIRECTORIES)
        if not allowed:
            return f"Error: Access denied for path: {p}"

    dest = Path(output_path) if output_path else paths[0].with_suffix(".pdf")

    try:
        import img2pdf
        image_paths = [str(p) for p in paths if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
        if not image_paths:
            return "Error: No supported image files (JPG, PNG) found in input paths."
        with open(dest, "wb") as f:
            f.write(img2pdf.convert(image_paths))
    except ImportError:
        # Fallback using Pillow
        from PIL import Image
        images = []
        for p in paths:
            img = Image.open(p).convert("RGB")
            images.append(img)
        if not images:
            return "Error: No images could be loaded."
        images[0].save(dest, save_all=True, append_images=images[1:])

    return f"PDF created at: {dest} ({len(paths)} page{'s' if len(paths) != 1 else ''})"
