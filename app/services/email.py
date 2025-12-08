import os
import resend
from dotenv import load_dotenv

# Cargar las variables del .env
load_dotenv()

# Configurar Resend con la clave del .env
resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

def send_email(to_email: str, subject: str, html_content: str):
    """
    Envía un correo electrónico usando Resend.
    Retorna el ID del email si fue exitoso, o None si falló.
    """
    try:
        print(f"📧 Intentando enviar correo a: {to_email}")
        
        params = {
            "from": f"Zerium App <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"✅ Correo enviado con éxito! ID: {email}")
        return email
    except Exception as e:
        print(f"❌ Error enviando correo: {str(e)}")
        return None

# Plantilla HTML para recuperar contraseña
def get_password_reset_template(reset_link: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f9fafb; padding: 40px 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin: 0;">Zerium</h1>
            </div>
            <h2 style="color: #1f2937; margin-bottom: 20px;">Recuperación de Contraseña</h2>
            <p style="color: #4b5563; line-height: 1.6;">Hola,</p>
            <p style="color: #4b5563; line-height: 1.6;">Hemos recibido una solicitud para restablecer tu contraseña. Si fuiste tú, haz clic en el botón de abajo:</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Restablecer Contraseña</a>
            </div>
            
            <p style="color: #6b7280; font-size: 0.9em;">Si no solicitaste este cambio, puedes ignorar este correo tranquilamente.</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="color: #9ca3af; font-size: 0.8em; text-align: center;">© 2025 Zerium Platform.</p>
        </div>
    </body>
    </html>
    """