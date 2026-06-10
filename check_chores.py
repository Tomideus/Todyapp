import json
import datetime
import smtplib
import os
from email.message import EmailMessage

def main():
    # Leer variables de entorno (GitHub Secrets)
    sender_email = os.environ.get("GMAIL_USER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    if not all([sender_email, app_password, recipient_email]):
        print("❌ Faltan variables de entorno. Revisa los GitHub Secrets.")
        return

    # Cargar datos
    with open("chores.json", "r", encoding="utf-8") as file:
        chores = json.load(file)

    today = datetime.date.today()
    overdue_tasks = []

    for chore in chores:
        last_date = datetime.datetime.strptime(chore["last_date"], "%Y-%m-%d").date()
        days_passed = (today - last_date).days
        
        if days_passed >= chore["frequency_days"]:
            overdue_tasks.append(
                f"🚨 *{chore['task_name']}*\n"
                f"   - Días vencido: {days_passed - chore['frequency_days']}\n"
                f"   - Última vez: {chore['last_done_by']} ({chore['last_date']})"
            )

    if not overdue_tasks:
        print("✅ Todo está limpio. No hay tareas vencidas.")
        return

    # Crear y enviar el correo
    msg = EmailMessage()
    msg['Subject'] = "🚨 Alerta: Tareas del hogar vencidas"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    email_body = "Hola!\n\nLas siguientes tareas están vencidas y necesitan atención:\n\n" + "\n\n".join(overdue_tasks) + "\n\nSaludos,\nTu sistema Home Tody 🏠"
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print("✅ Correo de recordatorio enviado con éxito.")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {str(e)}")

if __name__ == "__main__":
    main()