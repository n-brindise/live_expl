import warnings
import fire, os, json
import logging
from pointwise_in_time.utils import create_logger

if __name__ == '__main__':
    # create logger
    logger = create_logger(name="general", level = logging.DEBUG)

    # starting
    logger.info("STARTING")

    # launch process
    fire.Fire()

    logger.info("FINISHED")
    logger.handlers[0].flush()