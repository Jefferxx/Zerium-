from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# 1. Cargar configuración desde el archivo .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# 2. Configurar el contexto de encriptación (Hashing)
# Usamos 'bcrypt' porque es el estándar de oro para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """
    Compara una contraseña en texto plano (la que envía el usuario)
    con el hash guardado en la base de datos.
    Devuelve True si coinciden.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Toma una contraseña nueva y la convierte en un hash seguro
    para guardarla en la base de datos.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Genera un JSON Web Token (JWT) firmado.
    - data: Diccionario con los datos a guardar en el token (ej: email, rol).
    - expires_delta: Cuánto tiempo durará el token antes de expirar.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Default 15 min
    
    # Agregamos la fecha de expiración al contenido del token
    to_encode.update({"exp": expire})
    
    # Firmamos el token con nuestra clave secreta
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt