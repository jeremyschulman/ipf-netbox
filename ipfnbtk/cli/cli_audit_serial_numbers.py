from .cli_audit import cli_audit


@cli_audit.command('serial-numbers')
def cli_audit_serial_numbers():
    """
    Audit IPF serial-numbers against Netbox
    """
    pass

