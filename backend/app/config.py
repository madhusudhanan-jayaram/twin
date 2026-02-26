from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./cold_chain.db"
    openai_api_key: str = ""
    simulation_tick_seconds: float = 2.0
    simulation_minutes_per_tick: float = 5.0
    temperature_threshold_celsius: float = 6.0
    critical_temperature_celsius: float = 8.0
    warehouse_search_radius_miles: float = 50.0

    model_config = {"env_prefix": "COLD_CHAIN_", "env_file": ".env"}


settings = Settings()
