import secrets
import string
from fastapi_mail import FastMail, MessageSchema, MessageType  

from app.core.config import settings


async def send_email_async(subject: str, email_to: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype=MessageType.html
    )
    fm = FastMail(settings.mail.config)


    await fm.send_message(message)


def generate_verification_code(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))



def get_html_verify_message(token):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            margin: 0;
            background-color: #0f172a;
            font-family: sans-serif;
            color: #94a3b8;
        }}
        .main {{
            background-color: #1e293b;
            margin: 40px auto;
            max-width: 500px;
            border-radius: 12px;
            border: 1px solid #334155;
            text-align: center;
        }}
        .logo {{
            color: #4ade80;
            font-size: 24px;
            font-weight: bold;
            padding: 30px;
            display: block;
        }}
        .code-container {{
            background-color: #0f172a;
            border: 1px dashed #4ade80;
            margin: 20px 40px;
            padding: 20px;
            border-radius: 8px;
        }}
        .code-value {{
            font-family: monospace;
            font-size: 32px;
            color: #4ade80;
            letter-spacing: 5px;
        }}
        .footer {{
            font-size: 12px;
            color: #64748b;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="main">
        <span class="logo">SQLCraft</span>
        <h1 style="color: #f8fafc;">Подтвердите Email</h1>
        <p>Ваш код активации:</p>
        
        <div class="code-container">
            <span class="code-value">{token}</span>
        </div>
        
        <p style="font-size: 12px; padding: 0 20px;">Введите этот код в приложении для завершения регистрации.</p>
        <div class="footer">
            © 2026 SQLCraft
        </div>
    </div>
</body>
</html>
"""