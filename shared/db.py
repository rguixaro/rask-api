import os
import sys
import logging

from pymongo import MongoClient

logger = logging.getLogger()

_client = None


def get_db():
    global _client
    if _client is None:
        try:
            _client = MongoClient(os.environ["DB_URL"], connect=True)
            logger.info("SUCCESS: Connection to database instance succeeded")
        except Exception as e:
            logger.error("ERROR: Could not connect to database instance.")
            logger.error(e)
            sys.exit(1)
    return _client.get_database("Rask")
