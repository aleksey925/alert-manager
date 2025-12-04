import click
from aiohttp import web

from alert_manager.wsgi import app


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--host', default='0.0.0.0')  # noqa: S104
@click.option('--port', default=8080)
def serve(host: str, port: int) -> None:
    web.run_app(app=app, host=host, port=port)


if __name__ == '__main__':
    cli()
