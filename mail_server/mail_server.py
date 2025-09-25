from fastapi_mail import ConnectionConfig
import jwt
from datetime import datetime, timedelta, timezone
import os

username = os.getenv("MAIL_USERNAME")
password = os.getenv("MAIL_PASSWORD")
alias = os.getenv("MAIL_FROM")
secret = os.getenv("SECRET_KEY")

SECRET_KEY = secret
ALGORITHM = "HS256"

conf = ConnectionConfig(
    MAIL_USERNAME = username,
    MAIL_PASSWORD = password,
    MAIL_FROM = alias,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

def create_reset_token(email: str, expires_minutes: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_verification_token(email: str):
    expires = datetime.now(timezone.utc) + timedelta(minutes=1440)

    SECRET_KEY = os.getenv("SECRET_KEY")

    payload = {
        "sub": email,
        "type": "email_verification",
        "exp": expires
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return encoded_jwt