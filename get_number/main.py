import asyncio
import random
from pathlib import Path
from pprint import pprint
from typing import Optional

from loguru import logger
from telethon import events, TelegramClient
from pydantic import BaseModel, validator
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from config import config, BASE_DIR
from settings import init_logging
from telethon.tl.functions.channels import JoinChannelRequest

SESSION_PATH = Path(Path(__file__).parent, "sessions")


class Controller(BaseModel):
    number: str
    api_id: int
    api_hash: str
    client: Optional[TelegramClient]

    @validator("client", always=True)
    def create_client(cls, value, values):
        if isinstance(value, TelegramClient):
            return value
        path = str(Path(SESSION_PATH, f"{values['number']}_session.session"))
        logger.info(path)
        return TelegramClient(
            path,
            values["api_id"],
            values["api_hash"],
        )

    class Config:
        arbitrary_types_allowed = True

    def get_number_from_file(self) -> list:
        numbers = []
        for file in BASE_DIR.iterdir():
            if file.suffix == ".txt" and file.name != "usernames.txt":
                logger.debug(file)
                with open(file, encoding="utf-8") as f:
                    for line in f.readlines():
                        numbers.append(line.strip())

        return numbers

    def write_usernames(self, data: dict):
        str_data = ""
        for key, value in data.items():
            if not value:
                value = "Имя пользователя не указано"
                str_data += f"[{key}] --> {value}\n"
            elif value == "Профиль не найден":
                str_data += f"[{key}] --> \n"
            else:
                str_data += f"[{key}] --> @{value}\n"

        with open(Path(BASE_DIR, 'usernames.txt'), mode="a", encoding='utf-8') as f:
            f.write(str_data)

    async def start(self):
        try:
            await self.client.start()
        except Exception as e:
            logger.critical(e)
            path = str(Path(SESSION_PATH, f"{self.number}_session.session"))
            logger.info(path)
            self.client = TelegramClient(
                path,
                self.api_id,
                self.api_hash,
            )
            await self.client.start()

        data = {}
        numbers = self.get_number_from_file()
        for number in numbers:
            try:
                contact = InputPhoneContact(client_id=0, phone=number, first_name="ABC", last_name="abc")
                result = await self.client(ImportContactsRequest([contact]))
                logger.success(result)
                profile = await self.client.get_entity(number)
                try:
                    data[number] = profile.username
                except Exception as e:
                    data[number] = "Имя пользователя не указано"
                    logger.warning(e)
            except Exception as e:
                data[number] = "Профиль не найден"
                logger.warning(e)
        self.write_usernames(data)
        logger.info("Завершение скрипта")
        await self.client.disconnect()


def main():
    init_logging()

    # api_hash = "b5028e57a18d6a925b305047ea954f58"
    # api_id = 15607899
    print(config)
    client = Controller(**config.accounts[0].dict())
    asyncio.new_event_loop().run_until_complete(client.start())


if __name__ == '__main__':
    main()
