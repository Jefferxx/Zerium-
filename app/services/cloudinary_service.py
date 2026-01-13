import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración Global
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_file(file: UploadFile):
    """
    Sube un archivo a Cloudinary detectando automáticamente el tipo.
    """
    try:
        # CORRECCIÓN: 'resource_type="auto"' permite subir PDFs y que se visualicen bien.
        response = cloudinary.uploader.upload(
            file.file,
            folder="zerium_documents", 
            resource_type="auto"  # <--- ESTA ES LA CLAVE
        )
        
        return {
            "url": response.get("secure_url"),
            "public_id": response.get("public_id")
        }
    except Exception as e:
        print(f"Error subiendo a Cloudinary: {str(e)}")
        return None