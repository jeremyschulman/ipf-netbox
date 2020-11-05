#!/usr/bin/env python

import asyncio
from functools import lru_cache

import click
import yaml

from ipf_netbox.netbox.source import NetboxClient


async def create_interfaces(nb, dt_obj, dt_def, component):
    tasks = list()
    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        if_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: interface {if_name}: {_res.text}")
            return

        print(f"OK: interface {if_name}")

    for interface in dt_def[component]:
        interface["device_type"] = dt_obj["id"]
        task = asyncio.create_task(
            nb.post("/dcim/interface-templates/", json=interface),
            name=interface["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_console_server_ports(nb, dt_obj, dt_def, component):
    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        if_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: console-server-port {if_name}: {_res.text}")
            return

        print(f"OK: console-server-port {if_name}")

    tasks = list()

    for csport in dt_def[component]:
        csport["device_type"] = dt_obj["id"]
        task = asyncio.create_task(
            nb.post("/dcim/console-server-port-templates/", json=csport),
            name=csport["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_console_ports(nb, dt_obj, dt_def, component):
    tasks = list()

    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: console-port {port_name}: {_res.text}")
            return

        print(f"OK: console-port {port_name}")

    for consoleport in dt_def[component]:
        consoleport["device_type"] = dt_obj["id"]
        task = asyncio.create_task(
            nb.post("/dcim/console-port-templates/", json=consoleport),
            name=consoleport["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_power_ports(nb, dt_obj, dt_def, component):

    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: power-port {port_name}: {_res.text}")
            return

        print(f"OK: power-port {port_name}")

    tasks = list()

    for powerport in dt_def[component]:
        powerport["device_type"] = dt_obj["id"]
        task = asyncio.create_task(
            nb.post("/dcim/power-port-templates/", json=powerport),
            name=powerport["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_passthru_ports(nb, dt_obj, dt_def, component):
    ignore = "The fields device_type, name must make a unique set."

    # map port name to rear-port ID as this value is required for the front
    # port ID
    dt_id = dt_obj["id"]

    # first get the rear-port-IDs to see if any exist.
    res = await nb.get("/dcim/rear-port-templates/", params={"devicetype_id": dt_id})

    res.raise_for_status()
    rp_exists = res.json()
    rear_port_ids = {rec["name"]: rec["id"] for rec in rp_exists["results"]}

    def _on_rear_port(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: rear-port {port_name}: {_res.text}")
            return

        print(f"OK: rear-port {port_name}")
        if port_name in rear_port_ids:
            return

        body = _res.json()
        rear_port_ids[port_name] = body["id"]

    tasks = list()

    for rearport in dt_def["rear-ports"]:
        rearport["device_type"] = dt_obj["id"]

        task = asyncio.create_task(
            nb.post("/dcim/rear-port-templates/", json=rearport), name=rearport["name"],
        )
        task.add_done_callback(_on_rear_port)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    def _on_front_port(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: front-port {port_name}: {_res.text}")
            return

        print(f"OK: front-port {port_name}")

    for frontport in dt_def["front-ports"]:
        name = frontport["name"]
        frontport["device_type"] = dt_obj["id"]
        frontport["rear_port"] = rear_port_ids[name]
        task = asyncio.create_task(
            nb.post("/dcim/front-port-templates/", json=frontport), name=name
        )
        task.add_done_callback(_on_front_port)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


async def create_device_bays(nb, dt_id, devicebays):
    pass


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


async def create_power_outlets(nb, dt_obj, dt_def, component):
    # need the power outlets for cross-references into power outlets

    dt_id = dt_obj["id"]
    res = await nb.get("/dcim/power-port-templates", params={"devicetype_id": dt_id})
    res.raise_for_status()

    power_ports_ids = {rec["name"]: rec["id"] for rec in res.json()["results"]}

    tasks = list()

    ignore = "The fields device_type, name must make a unique set."

    def _report(_task):
        _res = _task.result()
        port_name = _task.get_name()

        if _res.is_error and ignore not in _res.text:
            print(f"FAIL: power-outlet {port_name}: {_res.text}")
            return

        print(f"OK: power-outlet {port_name}")

    for poweroutlet in dt_def[component]:
        poweroutlet["power_port"] = power_ports_ids[poweroutlet["power_port"]]
        poweroutlet["device_type"] = dt_id
        task = asyncio.create_task(
            nb.post("/dcim/power-outlet-templates/", json=poweroutlet),
            name=poweroutlet["name"],
        )
        task.add_done_callback(_report)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)


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
    "power-outlets": create_power_outlets,
    "device-bays": create_device_bays,
    "rear-ports": create_passthru_ports,
    # DO NOT have entry for 'front-ports' since the 'rear-ports' creator does
    # both front and rear together.
}


async def ensure_device_type(nb, dt_def):
    model = dt_def["model"]

    res = await nb.paginate(url="/dcim/device-types/", filters={"model": model})
    if res:
        print(f"OK: device-type: {model}")
        return res[0]

    mf_rec = await get_manufacturer(dt_def["manufacturer"])
    dt_def["manufacturer"] = mf_rec["id"]
    res = await nb.post("/dcim/device-types/", json=dt_def)
    res.raise_for_status()
    print(f"OK: device-type: {model}")
    return res.json()


async def create_device_type(nb: NetboxClient, dt_def: dict):

    dt_obj = await ensure_device_type(nb, dt_def)

    tasks = list()

    for component, creator in COMPONTENTS.items():
        if component in dt_def:
            tasks.append(creator(nb, dt_obj, dt_def, component))

    await asyncio.gather(*tasks)


# -----------------------------------------------------------------------------
#
#                                 CLI
#
# -----------------------------------------------------------------------------


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
