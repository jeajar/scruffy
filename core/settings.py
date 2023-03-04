from pydantic import AnyHttpUrl, EmailStr, BaseSettings

class Settings(BaseSettings):
    EMAIL_TEMPLATES_DIR: str = "email_templates/build"

settings = Settings()