from pydantic import BaseSettings


class Settings(BaseSettings):
    server_host: str = '0.0.0.0'
    server_port: int = 8000

    pg_user: str
    pg_pass: str
    pg_db_name: str
    pg_host: str
    pg_port: int

    jwt_secret: str
    jwt_algorithm: str = 'HS256'
    jwt_expiration: int = 1000

    redis_url: str


settings = Settings(
    _env_file='./.env',
    _env_file_encoding='utf-8'
)
