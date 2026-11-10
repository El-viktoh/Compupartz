import uuid

from django.core.exceptions import ValidationError
from PIL import Image

MAX_CHAT_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
# Decoders Pillow is allowed to try. Phone photos in the MPO container are opened by the JPEG decoder.
OPENABLE_FORMATS = ("JPEG", "PNG", "GIF", "WEBP")
# Results we accept (MPO is a JPEG container some phone cameras produce).
ALLOWED_IMAGE_FORMATS = {"JPEG", "MPO", "PNG", "GIF", "WEBP"}
_INVALID = "Please attach a valid image (JPG, PNG, GIF or WebP)."


def validate_chat_image(file):
    """Accept only a genuine, reasonably small raster image; everything else is refused."""
    if file.size > MAX_CHAT_IMAGE_BYTES:
        raise ValidationError("That image is too large. Please keep attachments under 5 MB.")
    try:
        file.seek(0)
        with Image.open(file, formats=OPENABLE_FORMATS) as img:
            image_format = img.format
            img.verify()
    except Exception:
        raise ValidationError(_INVALID)
    finally:
        try:
            file.seek(0)
        except Exception:
            pass
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(_INVALID)


def chat_image_upload_path(instance, filename):
    """Store under a random name with a whitelisted extension, never the uploader's filename."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = "png"
    return f"chat_images/{uuid.uuid4().hex}.{ext}"


def restrict_pillow_formats():
    """Make Pillow open only the image formats this site needs.

    Pillow auto-detects a file's real format from its bytes and ships decoders for dozens of rarely used
    formats (TIFF, BMP, FPX, MIC, PDF ...). Most of its published vulnerabilities live in those decoders,
    and visitors can upload images, so every format the site does not need is switched off for the whole
    project (booking photo, avatars, chat attachments).
    """
    try:
        Image.init()
        for name in list(Image.OPEN):
            if name not in ALLOWED_IMAGE_FORMATS:
                del Image.OPEN[name]
        Image.ID[:] = [name for name in Image.ID if name in ALLOWED_IMAGE_FORMATS]
    except AttributeError:
        # A future Pillow reorganised these internals; the per-upload validators above still apply.
        pass
