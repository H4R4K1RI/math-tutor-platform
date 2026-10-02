import asyncio
import smtplib
from datetime import datetime
from email.message import EmailMessage

from app.shared.config import settings
from app.shared.logger import logger


def _send_email_sync(to_email: str, subject: str, text: str, html: str) -> bool:
    """Синхронная отправка email (выполняется в executor)."""
    SMTP_HOST = settings.SMTP_HOST or "smtp.beget.com"
    SMTP_PORT = settings.SMTP_PORT or 465
    SMTP_USER = settings.SMTP_USER
    SMTP_PASSWORD = settings.SMTP_PASSWORD
    FROM_EMAIL = settings.SMTP_FROM_EMAIL or "noreply@tutor-platform.ru"
    FROM_NAME = settings.SMTP_FROM_NAME or "Math Tutor Platform"

    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("SMTP credentials not configured")
        return False

    msg = EmailMessage()
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False


async def send_reminder_email(
    to_email: str,
    student_name: str,
    lesson_title: str,
    start_time: datetime,
    reminder_type: str,
):
    """Отправить напоминание о уроке (async)."""

    start_time_str = start_time.strftime("%d.%m.%Y в %H:%M")

    if reminder_type == "day_before":
        subject = f"🔔 Напоминание: урок завтра в {start_time.strftime('%H:%M')}"
        preview = f"Урок состоится завтра в {start_time_str}"
    else:
        subject = "🔔 Напоминание: урок через час"
        preview = f"Урок состоится сегодня в {start_time_str}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Напоминание об уроке</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #1e3a2f 0%, #2d5a3f 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .lesson-details {{ background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>📐 Math Tutor Platform</h1></div>
            <div class="content">
                <h2>Здравствуйте, {student_name}!</h2>
                <p>{preview}</p>
                <div class="lesson-details">
                    <strong>📚 Тема:</strong> {lesson_title or 'Урок'}<br>
                    <strong>⏰ Время:</strong> {start_time_str}
                </div>
                <p>Пожалуйста, подготовьтесь к занятию заранее.</p>
            </div>
            <div class="footer"><p>© 2026 Math Tutor Platform. Все права защищены.</p></div>
        </div>
    </body>
    </html>
    """

    text_content = (
        f"Напоминание: {preview}\n\n"
        f"Тема: {lesson_title or 'Урок'}\n"
        f"Время: {start_time_str}"
    )

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        _send_email_sync,
        to_email,
        subject,
        text_content,
        html_content,
    )


async def send_payment_reminder_email(
    to_email: str,
    student_name: str,
    debt_amount: float,
    teacher_name: str,
):
    """Отправить напоминание о задолженности (async)."""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Напоминание об оплате</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%); color: white; padding: 30px; text-align: center; }}
            .content {{ padding: 40px 30px; }}
            .debt-box {{ background-color: #fce4e4; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
            .debt-amount {{ font-size: 32px; font-weight: bold; color: #c0392b; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>💰 Уведомление об оплате</h1></div>
            <div class="content">
                <h2>Здравствуйте, {student_name}!</h2>
                <p>У вас есть задолженность перед репетитором <strong>{teacher_name}</strong>.</p>
                <div class="debt-box">
                    <div class="debt-amount">{debt_amount:.2f} ₽</div>
                    <div>сумма задолженности</div>
                </div>
                <p>Пожалуйста, свяжитесь с репетитором для уточнения деталей оплаты.</p>
            </div>
            <div class="footer"><p>© 2026 Math Tutor Platform. Все права защищены.</p></div>
        </div>
    </body>
    </html>
    """

    text_content = (
        f"Уважаемый {student_name}, у вас есть задолженность перед репетитором "
        f"{teacher_name} в размере {debt_amount:.2f} ₽."
    )

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        _send_email_sync,
        to_email,
        "💰 Напоминание об оплате",
        text_content,
        html_content,
    )