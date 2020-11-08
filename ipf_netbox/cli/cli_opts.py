import click

opt_force_primary_ip = click.option(
    "--force-primary-ip",
    is_flag=True,
    help="When IP is already set, update IP if different",
)

opt_dry_run = click.option("--dry-run", is_flag=True, help="Dry-run mode")

opt_device_filter = click.option(
    "--filter", "filters", help="IPF device inventory filter expression",
)
