from importlib import metadata
import click


@click.group()
@click.version_option(metadata.version('ipfnbtk'))
def cli():
    pass
