# test_email.py
from app.services.email import send_email, get_password_reset_template

# --- PON TU CORREO PERSONAL AQUÍ PARA VER SI LLEGA ---
DESTINO = "jefferson.jordan2004@gmail.com" 

print("🚀 Iniciando prueba de envío de correo...")

# Usamos la plantilla HTML que ya creaste
html_content = get_password_reset_template("https://zerium.ec/recuperar?token=12345")

# Intentamos enviar
resultado = send_email(DESTINO, "Prueba de Configuración Zerium", html_content)

if resultado:
    print(f"✅ ¡Éxito! El ID del correo es: {resultado}")
    print("revisa tu bandeja de entrada (y SPAM).")
else:
    print("❌ Falló el envío. Revisa tu API Key en el archivo .env")