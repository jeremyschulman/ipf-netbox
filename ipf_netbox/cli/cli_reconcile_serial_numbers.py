from .cli_reconcile import cli_reconcile


@cli_reconcile.command("serial-numbers")
def serial_numbers():
    """
    Copy IPF serial-numbers into Netbox device records.
    """
    pass
