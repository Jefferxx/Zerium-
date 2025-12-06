from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import user as user_crud
from app import auth_utils

# Creamos el router para las rutas de autenticación
router = APIRouter(
    tags=["Authentication"]
)

@router.post("/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint oficial de Login (Estándar OAuth2).
    
    Recibe:
    - username: El email del usuario (formato x-www-form-urlencoded)
    - password: La contraseña en texto plano
    
    Devuelve:
    - access_token: El JWT firmado
    - token_type: "bearer"
    """
    
    # 1. Buscar usuario por email (username en el formulario OAuth2)
    user = user_crud.get_user_by_email(db, email=form_data.username)
    
    # 2. Verificar si el usuario existe y si la contraseña es correcta
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        # Si falla, devolvemos un error 401 (No autorizado)
        # El header WWW-Authenticate es obligatorio por el estándar
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 3. Si todo está bien, generamos el token
    # Calculamos cuándo expira
    access_token_expires = auth_utils.timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Creamos el token con datos extra (email y rol)
    access_token = auth_utils.create_access_token(
        data={"sub": user.email, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    # 4. Devolvemos el token al usuario
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,        # <--- AGREGADO
        "user_id": user.id        # <--- AGREGADO (Útil para después)
    }