import asyncio
from typing import Generator, Union
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from datetime import datetime
import dateparser
from .config import config
import logging


logger = logging.getLogger(__name__)


class Storage:
    """Basic storage to handle results during the processing. """
    def __init__(self) -> None:
        self._data = []

    def append(self, value: dict) -> None:
        self._data.append(value)

    def flush(self) -> list[dict]:
        out = self._data
        self._data = []

        return out

    def __repr__(self) -> str:
        return self._data.__repr__()

    def __len__(self) -> int:
        return len(self._data)


def asynciotask_handler(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass    # Task cancellation should not be logged as an error.
    except Exception as err:
        logger.exception(f"Exception raised by task '{task.get_name()}'")

async def _es_gendata(results: list[dict]) -> Generator[dict, None, None]:
    for res in results:
        yield {
            "_index": config.es.index,
            # "_type": "_doc",
            **res
        }

async def es_bulk(es: AsyncElasticsearch, results: list) -> None:
    if not results:
        return
    
    _, errors = await async_bulk(es, _es_gendata(results))

    if errors:
        logger.error(f"ES bulk index error: {errors}")

def convert_datetime(date: str) -> Union[datetime, None]:
    return dateparser.parse(date)
