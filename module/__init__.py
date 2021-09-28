from .config import config
from .transforms import QuotesExtract, FastText
from .utils import asynciotask_handler, es_bulk, Storage

import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s -  %(name)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(config.logger.level)