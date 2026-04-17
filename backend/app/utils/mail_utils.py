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


    await fm.send_message(message, from_display_name="SqlCraft Support")


def generate_verification_code(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))