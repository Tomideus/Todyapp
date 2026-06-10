import json
import datetime
import smtplib
import os
from email.message import EmailMessage

def main():
    sender_email = os.environ.get("GMAIL_USER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    if not all([sender_email, app_password, recipient_email]):
        print("❌ Missing environment variables. Check GitHub Secrets.")
        return

    # Cargar historial
    try:
        with open("history.json", "r", encoding="utf-8") as file:
            history = json.load(file)
    except FileNotFoundError:
        print("❌ history.json not found.")
        return

    # Calcular el mes anterior
    today = datetime.date.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
    
    target_year = last_day_of_previous_month.year
    target_month = last_day_of_previous_month.month
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    month_name = month_names[target_month - 1]

    # Calcular puntajes del mes anterior
    scores = {}
    for entry in history:
        entry_date = datetime.datetime.strptime(entry["date"], "%Y-%m-%d").date()
        if entry_date.year == target_year and entry_date.month == target_month:
            user = entry["user"]
            points = entry.get("points", 0)
            scores[user] = scores.get(user, 0) + points

    if not scores:
        print(f"✅ No activities in {month_name} {target_year}. No winner to announce.")
        return

    # Encontrar al ganador
    winner = max(scores.items(), key=lambda x: x[1])
    
    # Crear el correo
    msg = EmailMessage()
    msg['Subject'] = f"🏆 Monthly Winner: {month_name} {target_year}!"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    email_body = f"""Hello!

🎉 The monthly cleaning champion has been announced!

🏆 WINNER: {winner[0]}
📊 Points: {winner[1]}

Final standings for {month_name} {target_year}:
"""
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (user, score) in enumerate(sorted_scores, 1):
        email_body += f"{i}. {user}: {score} points\n"
    
    email_body += f"\nCongratulations to the winner! 🎊\n\nBest,\nYour Home Tody App 🏠"
    
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print(f"✅ Monthly winner email sent successfully! Winner: {winner[0]}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")

if __name__ == "__main__":
    main()
