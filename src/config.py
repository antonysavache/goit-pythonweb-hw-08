from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/contacts_db"
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 30
    cors_origins: str = "*"
    app_base_url: str = "http://127.0.0.1:8000"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""


settings = Settings()
