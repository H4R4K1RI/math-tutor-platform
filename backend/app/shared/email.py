import asyncio
import smtplib
from email.message import EmailMessage

from app.shared.config import settings
from app.shared.logger import logger
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def generate_verification_token(email: str) -> str:
    return serializer.dumps(email, salt="email-verification")


def verify_email_token(token: str, expiration: int = 3600) -> str | None:
    try:
        email = serializer.loads(token, salt="email-verification", max_age=expiration)
        return email
    except Exception:
        return None


def _send_email_sync(to_email: str, subject: str, text: str, html: str) -> bool:
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


async def send_verification_email(email: str, token: str):
    verify_url = f"https://tutor-platform.ru/api/auth/verify-email?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Подтверждение email</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a2f 0%, #2d5a3f 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; text-align: center; }}
            .content p {{ color: #333; line-height: 1.6; margin-bottom: 30px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #2e7d5e 0%, #1e5a44 100%); color: white; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #eee; }}
            .warning {{ font-size: 12px; color: #999; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>📐 Math Tutor Platform</h1></div>
            <div class="content">
                <h2>Добро пожаловать!</h2>
                <p>Для завершения регистрации и подтверждения вашего email, пожалуйста, нажмите на кнопку ниже:</p>
                <a href="{verify_url}" class="button">Подтвердить email</a>
                <p class="warning">Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.</p>
                <p class="warning">Ссылка действительна в течение 1 часа.</p>
            </div>
            <div class="footer">
                <p>© 2026 Math Tutor Platform. Все права защищены.</p>
                <p>Это автоматическое письмо, отвечать на него не нужно.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"Для подтверждения email перейдите по ссылке: {verify_url}"

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        _send_email_sync,
        email,
        "Подтверждение email",
        text_content,
        html_content,
    )