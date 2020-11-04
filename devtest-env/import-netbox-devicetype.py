#!/usr/bin/env python

import asyncio
from functools import lru_cache

import click
import yaml

from ipf_netbox.netbox.source import NetboxClient


# def readYAMl(files):
#     deviceTypes = []
#     manufacturers = []
#     for file in files:
#         with open(file, 'r') as stream:
#             try:
#                 data = yaml.safe_load(stream)
#             except yaml.YAMLError as exc:
#                 print(exc)
#             manufacturer = data['manufacturer']
#             data['manufacturer'] = {}
#             data['manufacturer']['name'] = manufacturer
#             data['manufacturer']['slug'] = manufacturer.lower()
#         deviceTypes.append(data)
#         manufacturers.append(manufacturer)
#     return deviceTypes
#

# def createManufacturers(vendors, nb):
#     for vendor in vendors:
#         try:
#             manGet = nb.dcim.manufacturers.get(name=vendor["name"])
#             if manGet:
#                 print(f'Manufacturer Exists: {manGet.name} - {manGet.id}')
#             else:
#                 manSuccess = nb.dcim.manufacturers.create(vendor)
#                 print(f'Manufacturer Created: {manSuccess.name} - {manSuccess.id}')
#                 counter.update({'manufacturer':1})
#         except pynetbox.RequestError as e:
#             print(e.error)


async def create_interfaces(nb, dt_id, interfaces):
    tasks = list()
    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        if_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: interface {if_name}: {_res.text}")
            return

        print(f"OK: interface {if_name}")

    for interface in interfaces:
        interface["device_type"] = dt_id
        task = asyncio.create_task(
            nb.post("/dcim/interface-templates/", json=interface),
            name=interface["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_console_server_ports(nb, dt_id, consoleserverports):
    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        if_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: console-server-port {if_name}: {_res.text}")
            return

        print(f"OK: console-server-port {if_name}")

    tasks = list()

    for csport in consoleserverports:
        csport["device_type"] = dt_id
        task = asyncio.create_task(
            nb.post("/dcim/console-server-port-templates/", json=csport),
            name=csport["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_console_ports(nb, dt_id, consoleports):
    tasks = list()

    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: console-port {port_name}: {_res.text}")
            return

        print(f"OK: console-port {port_name}")

    for consoleport in consoleports:
        consoleport["device_type"] = dt_id
        task = asyncio.create_task(
            nb.post("/dcim/console-port-templates/", json=consoleport),
            name=consoleport["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_power_ports(nb, dt_id, powerports):

    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: power-port {port_name}: {_res.text}")
            return

        print(f"OK: power-port {port_name}")

    tasks = list()

    for powerport in powerports:
        powerport["device_type"] = dt_id
        task = asyncio.create_task(
            nb.post("/dcim/power-port-templates/", json=powerport),
            name=powerport["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


# def createConsoleServerPorts(consoleserverports, deviceType, nb):
#     for csport in consoleserverports:
#         csport['device_type'] = deviceType
#         try:
#             cspGet = nb.dcim.console_server_port_templates.get(devicetype_id=deviceType, name=csport["name"])
#             if cspGet:
#                 print(f'Console Server Port Template Exists: {cspGet.name} - {cspGet.type} - {cspGet.device_type.id} - {cspGet.id}')
#             else:
#                 cspSuccess = nb.dcim.console_server_port_templates.create(csport)
#                 print(f'Console Server Port Created: {cspSuccess.name} - {cspSuccess.type} - {cspSuccess.device_type.id} - {cspSuccess.id}')
#                 counter.update({'updated':1})
#         except pynetbox.RequestError as e:
#             print(e.error)

# def createFrontPorts(frontports, deviceType, nb):
#     for frontport in frontports:
#         frontport['device_type'] = deviceType
#         try:
#             fpGet = nb.dcim.front_port_templates.get(devicetype_id=deviceType, name=frontport["name"])
#             if fpGet:
#                 print(f'Front Port Template Exists: {fpGet.name} - {fpGet.type} - {fpGet.device_type.id} - {fpGet.id}')
#             else:
#                 rpGet = nb.dcim.rear_port_templates.get(devicetype_id=deviceType, name=frontport["rear_port"])
#                 if rpGet:
#                     frontport['rear_port'] = rpGet.id
#                     fpSuccess = nb.dcim.front_port_templates.create(frontport)
#                     print(f'Front Port Created: {fpSuccess.name} - {fpSuccess.type} - {fpSuccess.device_type.id} - {fpSuccess.id}')
#                 counter.update({'updated':1})
#         except pynetbox.RequestError as e:
#             print(e.error)

# def createRearPorts(rearports, deviceType, nb):
#     for rearport in rearports:
#         rearport['device_type'] = deviceType
#         try:
#             rpGet = nb.dcim.rear_port_templates.get(devicetype_id=deviceType, name=rearport["name"])
#             if rpGet:
#                 print(f'Rear Port Template Exists: {rpGet.name} - {rpGet.type} - {rpGet.device_type.id} - {rpGet.id}')
#             else:
#                 rpSuccess = nb.dcim.rear_port_templates.create(rearport)
#                 print(f'Rear Port Created: {rpSuccess.name} - {rpSuccess.type} - {rpSuccess.device_type.id} - {rpSuccess.id}')
#                 counter.update({'updated':1})
#         except pynetbox.RequestError as e:
#             print(e.error)

# def createDeviceBays(devicebays, deviceType, nb):
#     for devicebay in devicebays:
#         devicebay['device_type'] = deviceType
#         try:
#             dbGet = nb.dcim.device_bay_templates.get(devicetype_id=deviceType, name=devicebay["name"])
#             if dbGet:
#                 print(f'Device Bay Template Exists: {dbGet.name} - {dbGet.device_type.id} - {dbGet.id}')
#             else:
#                 dbSuccess = nb.dcim.device_bay_templates.create(devicebay)
#                 print(f'Device Bay Created: {dbSuccess.name} - {dbSuccess.device_type.id} - {dbSuccess.id}')
#                 counter.update({'updated':1})
#         except pynetbox.RequestError as e:
#             print(e.error)

# def createPowerOutlets(poweroutlets, deviceType, nb):
#     for poweroutlet in poweroutlets:
#         try:
#             poGet = nb.dcim.power_outlet_templates.get(devicetype_id=deviceType, name=poweroutlet["name"])
#             if poGet:
#                 print(f'Power Outlet Template Exists: {poGet.name} - {poGet.type} - {poGet.device_type.id} - {poGet.id}')
#             else:
#                 try:
#                     ppGet = nb.dcim.power_port_templates.get(devicetype_id=deviceType)
#                     if ppGet:
#                         poweroutlet["power_port"] = ppGet.id
#                         poweroutlet["device_type"] = deviceType
#                         poSuccess = nb.dcim.power_outlet_templates.create(poweroutlet)
#                         print(f'Power Outlet Created: {poSuccess.name} - {poSuccess.type} - {poSuccess.device_type.id} - {poSuccess.id}')
#                         counter.update({'updated':1})
#                 except:
#                     poweroutlet["device_type"] = deviceType
#                     poSuccess = nb.dcim.power_outlet_templates.create(poweroutlet)
#                     print(f'Power Outlet Created: {poSuccess.name} - {poSuccess.type} - {poSuccess.device_type.id} - {poSuccess.id}')
#                     counter.update({'updated':1})
#         except pynetbox.RequestError as e:
#             print(e.error)


@lru_cache()
async def get_manufacturer(name):
    async with NetboxClient() as nb:
        res = await nb.get("/dcim/manufacturers", params={"name": name})
        res.raise_for_status()
        body = res.json()
        return body["results"][0] if body["count"] else None


COMPONTENTS = {
    "interfaces": create_interfaces,
    "console-ports": create_console_ports,
    "power-ports": create_power_ports,
    "power-port": create_power_ports,
    "console-server-ports": create_console_server_ports,
    # 'power-outlets': 1,
    # 'rear-ports': 1,
    # 'front-ports': 1,
    # 'device-bays': 1,
}


async def ensure_device_type(nb, dt_def):
    model = dt_def["model"]

    res = await nb.paginate(url="/dcim/device-types/", filters={"model": model})
    if res:
        print(f"EXISTS: device-type: {model}")
        return res[0]

    mf_rec = await get_manufacturer(dt_def["manufacturer"])
    dt_def["manufacturer"] = mf_rec["id"]
    res = await nb.post("/dcim/device-types/", json=dt_def)
    res.raise_for_status()
    print(f"CREATE: device-type: {model}")
    return res.json()


async def create_device_type(nb: NetboxClient, dt_def: dict):

    dt_obj = await ensure_device_type(nb, dt_def)
    dt_id = dt_obj["id"]

    tasks = list()

    for component, creator in COMPONTENTS.items():
        if component in dt_def:
            tasks.append(creator(nb, dt_id, dt_def[component]))

    await asyncio.gather(*tasks, return_exceptions=True)


@click.command()
@click.option(
    "--file", "file_", help="Device-Type YAML file", required=True, type=click.File()
)
def cli_load_file(file_):
    dt_def = yaml.safe_load(file_)
    nb = NetboxClient()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_device_type(nb, dt_def))
    asyncio.run(nb.aclose())


if __name__ == "__main__":
    cli_load_file()
