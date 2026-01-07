import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

def upload_file(file, folder="zerium_documents"):
    try:
        # Subida directa desde la memoria RAM
        response = cloudinary.uploader.upload(file.file, folder=folder, resource_type="auto")
        return {
            "url": response.get("secure_url"),
            "public_id": response.get("public_id")
        }
    except Exception as e:
        print(f"Error Cloudinary: {str(e)}")
        return None