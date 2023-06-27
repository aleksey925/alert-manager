import logging
from logging.config import dictConfig

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.types import Processor

from alert_manager.libs.structlog_utils import TimeStamper

json_renderer = JSONRenderer(ensure_ascii=False)
simple_renderer = ConsoleRenderer(colors=True)


def get_processors(timestamp_fmt: str | None) -> list[Processor]:
    return [
        TimeStamper(fmt=timestamp_fmt),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.format_exc_info,
    ]


def _init_structlog(log_level: int, processors: list[Processor]) -> None:
    structlog.configure(
        cache_logger_on_first_use=True,
        processors=[*processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(min_level=log_level),
    )


def _init_logging(
    log_level: int, processors: list[Processor], renderer: ConsoleRenderer | JSONRenderer
) -> None:
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    '()': structlog.stdlib.ProcessorFormatter,
                    'processors': [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        renderer,
                    ],
                    'foreign_pre_chain': processors,
                },
            },
            'handlers': {
                'default': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                },
            },
            'loggers': {
                '': {
                    'handlers': ['default'],
                    'level': log_level,
                }
            },
        }
    )


def init_logger(
    log_format: str,
    log_level: str,
    log_timestamp_format: str | None,
) -> None:
    level = getattr(logging, log_level.upper())
    renderer: ConsoleRenderer | JSONRenderer = (
        json_renderer if log_format == 'json' else simple_renderer
    )

    processors = get_processors(log_timestamp_format)
    _init_logging(level, processors, renderer)
    _init_structlog(level, processors)
