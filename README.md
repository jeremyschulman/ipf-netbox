** WORK IN PROGRESS **

# IP Fabric <-> Netbox Utility

This package provides a CLI and python modules useful to integrate between the
[IP Fabric](https://ipfabric.io/) product and the
[Netbox](https://netbox.readthedocs.io/) project.

The premise of this tool is that Netbox represents the "network as expected" and
IP Fabric contains information about the network "as built" or "actual".  I want to be able
to "synchronize" aspects of IP Fabric database into Netbox.  There are a few motivating reasons:

1.  New deployment of Netbox and I want to use my existing network as the basis for the initial Netbox
datatset.

2.  Network engineers make changes to the network via CLI, and I want to "reconcile" those
changes into the Netbox system.

# Tasks

The `ipf-netbox` tool provides a number tasks that perform checks and synchronizations.  The
following tasks are planned for this tool.

* `ensure-sites` - Ensure that Netbox contains the same Sites as provided in IP Fabric
* `ensure-devices` - Ensure that Netbox contains the same Devices as provided in IP Fabric.  Check the devie
site, and facts about the device such as vendor, model, and serial-number.
* `ensure-interfaces` - Ensure that Netbox devices contains the same set of data as provided in IP Fabric.
The data includes the **full interface-name** and interface-description.
* `ensure-ipaddrs` - Ensure that Netbox IPAM system includes the IP addresses defined in IP Fabric as
"managed IP addresses".  Ensure that the IP addresses are correctly assgined to Netbox device interfaces.


