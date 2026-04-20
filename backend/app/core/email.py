import os
import smtplib
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer
from app.core.config import settings

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def generate_verification_token(email: str) -> str:
    return serializer.dumps(email, salt="email-verification")

def verify_email_token(token: str, expiration: int = 3600) -> str | None:
    try:
        email = serializer.loads(token, salt="email-verification", max_age=expiration)
        return email
    except Exception:
        return None

async def send_verification_email(email: str, token: str):
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.beget.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@tutor-platform.ru")
    FROM_NAME = os.getenv("SMTP_FROM_NAME", "Math Tutor Platform")
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("SMTP credentials not configured")
        return
    
    verify_url = f"https://tutor-platform.ru/api/auth/verify-email?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Подтверждение email</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1e3a2f 0%, #2d5a3f 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .content p {{
                color: #333;
                line-height: 1.6;
                margin-bottom: 30px;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #2e7d5e 0%, #1e5a44 100%);
                color: white;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 8px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .button:hover {{
                background: linear-gradient(135deg, #1e5a44 0%, #2e7d5e 100%);
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-top: 1px solid #eee;
            }}
            .warning {{
                font-size: 12px;
                color: #999;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📐 Math Tutor Platform</h1>
            </div>
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
    
    msg = EmailMessage()
    msg.set_content(f"Для подтверждения email перейдите по ссылке: {verify_url}")
    msg.add_alternative(html_content, subtype='html')
    msg['Subject'] = 'Подтверждение email'
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = email
    
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Verification email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")