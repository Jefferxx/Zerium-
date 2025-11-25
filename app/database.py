from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# 1. Cargar variables de entorno desde el archivo .env
load_dotenv()

# 2. Obtener la URL de conexión
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Validar que la URL exista
if not DATABASE_URL:
    raise ValueError("No se encontró la variable DATABASE_URL en el archivo .env")

# 4. Solución para Supabase: SQLAlchemy necesita 'postgresql://' en lugar de 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)  
# 5. Crear el motor de la base de datos (El corazón de la conexión)
engine = create_engine(DATABASE_URL)

# 6. Crear la sesión local (La herramienta para hacer consultas)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 7. Clase base para nuestros modelos de tablas
Base = declarative_base()

# 8. Dependencia para obtener la DB en cada petición (Función auxiliar)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()