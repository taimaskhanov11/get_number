import yaml
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent.parent


class Account(BaseModel):
    number: str
    api_id: int
    api_hash: str


class Config(BaseModel):
    accounts: list[Account]


def load_config():
    with open(Path(BASE_DIR, "config.yml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = Config(**load_config())
