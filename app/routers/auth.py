from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import user as user_crud
from app import auth_utils
# Importamos los nuevos schemas y el servicio de email
from app.schemas.user import PasswordResetRequest, PasswordResetConfirm
from app.services.email import send_email, get_password_reset_template

# Creamos el router para las rutas de autenticación
router = APIRouter(
    tags=["Authentication"]
)

# 1. LOGIN (EXISTENTE)
@router.post("/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint oficial de Login (Estándar OAuth2).
    """
    # 1. Buscar usuario por email
    user = user_crud.get_user_by_email(db, email=form_data.username)
    
    # 2. Verificar credenciales
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generar token
    access_token_expires = auth_utils.timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.email, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    # 4. Devolver respuesta
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

# 2. SOLICITAR RECUPERACIÓN (NUEVO)
@router.post("/auth/forgot-password", status_code=200)
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Envía un correo con el link de recuperación si el usuario existe.
    """
    user = user_crud.get_user_by_email(db, email=request.email)
    
    # Si no existe, devolvemos mensaje genérico por seguridad
    if not user:
        return {"message": "Si el correo existe, se ha enviado un enlace de recuperación."}

    # Generar token de recuperación (válido por 15 min)
    access_token_expires = auth_utils.timedelta(minutes=15)
    # 'type': 'reset' diferencia este token de uno de login normal
    reset_token = auth_utils.create_access_token(
        data={"sub": user.email, "type": "reset"}, 
        expires_delta=access_token_expires
    )

    # Crear el Link (Apunta al Frontend)
    # IMPORTANTE: Cuando despliegues el frontend, cambiarás localhost por tu dominio vercel
    reset_link = f"https://zerium-frontend.vercel.app/reset-password?token={reset_token}"
    
    # Preparar y enviar correo
    html_content = get_password_reset_template(reset_link)
    send_email(user.email, "Recupera tu acceso a Zerium", html_content)

    return {"message": "Si el correo existe, se ha enviado un enlace de recuperación."}

# 3. RESTABLECER CONTRASEÑA (NUEVO)
@router.post("/auth/reset-password", status_code=200)
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Recibe el token y la nueva contraseña para actualizarla.
    """
    try:
        # Decodificar el token
        payload = auth_utils.jwt.decode(data.token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        
        # Validar que sea un token de tipo 'reset'
        if email is None or token_type != "reset":
            raise HTTPException(status_code=400, detail="Token inválido")
            
    except Exception:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    # Buscar usuario
    user = user_crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Hashear la nueva contraseña y guardar
    hashed_password = auth_utils.get_password_hash(data.new_password)
    user.password_hash = hashed_password
    db.commit()

    return {"message": "Contraseña actualizada correctamente"}