import cloudinary
import cloudinary.uploader

from src.config import settings

_is_configured = bool(
    settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret
)

if _is_configured:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def upload_avatar(file_path: str, public_id: str) -> str:
    if not _is_configured:
        raise ValueError("Cloudinary is not configured")

    response = cloudinary.uploader.upload(
        file_path,
        public_id=public_id,
        overwrite=True,
        transformation=[{"width": 250, "height": 250, "crop": "fill"}],
    )
    return response["secure_url"]
