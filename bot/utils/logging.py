# coding=utf-8
"""Formats logging for bot"""
import logging

import colorlog


def setup_logger(logger_name: str):
    """
    Setting up logging.
    """
    formatter = colorlog.LevelFormatter(
        fmt={
            "DEBUG": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "INFO": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "WARNING": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "ERROR": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "CRITICAL": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
        },
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red"
        },
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(logger_name)
    logger.level = logging.INFO

    # Set the root logger level, too.
    logging.root.setLevel(logger.level)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
