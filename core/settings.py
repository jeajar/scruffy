from pydantic import AnyHttpUrl, EmailStr, BaseSettings
from core.config import config

class Settings(BaseSettings):
    EMAIL_TEMPLATES_DIR: str = "email_templates/build"
    EMAIL_HOST: str = config['email']['host'].get()
    EMAIL_PORT: int = config['email']['port'].get()
    EMAIL_TLS: bool = config['email']['tls'].get()
    EMAIL_USER: EmailStr = config['email']['user'].get()
    EMAIL_PASSWORD: str = config['email']['password'].get()
    EMAIL_FROM_NAME: str = config['email']['from_name'].get()
    EMAIL_FROM_EMAIL: EmailStr = config['email']['from'].get()

    LOG_LEVEL: str = config['app']['log_level'].get()

settings = Settings()