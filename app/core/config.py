from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "RCN_"}

    wfs_base_url: str = "https://mapy.geoportal.gov.pl/wss/service/rcn"
    upstream_connect_timeout: float = 10.0
    upstream_read_timeout: float = 30.0
    upstream_max_retries: int = 2
    upstream_retry_backoff: tuple[float, ...] = (0.5, 1.5)

    cache_ttl_features: int = 300
    cache_ttl_metadata: int = 86400
    cache_max_size: int = 256

    rate_limit: str = "60/minute"
    max_page_size: int = 500
    default_page_size: int = 100


settings = Settings()
