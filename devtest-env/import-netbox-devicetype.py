#!/usr/bin/env python

import asyncio
from glob import glob
from functools import wraps
import click
import yaml  # noqa: install pyyaml in your virtualenv

from ipf_netbox.netbox.source import NetboxClient

IGNORE = "The fields device_type, name must make a unique set."


def creator(label):
    def decorator(func):
        @wraps(func)
        async def wrapper(nb, dt_obj, dt_def, component):
            tasks = list()

            def _report(_task):
                _res = _task.result()
                if_name = _task.get_name()

                if _res.is_error and IGNORE not in _res.text:
                    print(f"FAIL: {label} {if_name}: {_res.text}")
                    return

                print(f"OK: {label} {if_name}")

            for comp_def in dt_def[component]:
                comp_def["device_type"] = dt_obj["id"]
                task = func(nb, comp_def)
                task.add_done_callback(_report)
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        return wrapper

    return decorator


@creator(label="interface")
def create_interfaces(nb, comp_def):
    return asyncio.create_task(
        nb.post("/dcim/interface-templates/", json=comp_def), name=comp_def["name"]
    )


@creator(label="console-server-port")
def create_console_server_ports(nb, comp_def):
    return asyncio.create_task(
        nb.post("/dcim/console-server-port-templates/", json=comp_def),
        name=comp_def["name"],
    )


@creator(label="console-port")
def create_console_ports(nb, comp_def):
    return asyncio.create_task(
        nb.post("/dcim/console-port-templates/", json=comp_def), name=comp_def["name"],
    )


@creator(label="power-port")
def create_power_ports(nb, comp_def):
    return asyncio.create_task(
        nb.post("/dcim/power-port-templates/", json=comp_def), name=comp_def["name"],
    )


async def create_passthru_ports(nb, dt_obj, dt_def, component):

    # -------------------------------------------------------------------------
    # first get the rear-port-IDs to see if any exist. map port name to
    # rear-port ID as this value is required for the front port ID
    # -------------------------------------------------------------------------

    res = await nb.get(
        "/dcim/rear-port-templates/", params={"devicetype_id": dt_obj["id"]}
    )
    res.raise_for_status()
    rp_exists = res.json()

    rear_port_ids = {rec["name"]: rec["id"] for rec in rp_exists["results"]}

    # -------------------------------------------------------------------------
    # next create rear-ports
    # -------------------------------------------------------------------------

    def _record_rp_id(_task):
        _res = _task.result()
        if _res.is_error:
            # we can ignore the errors here since any valid errors are already
            # trapped in the creator decorator.  We need this check here,
            # however, to discard the create-exists falure response.
            return

        body = _res.json()
        rear_port_ids[body["name"]] = body["id"]

    @creator(label="rear-port")
    def _create_rear_port(_nb, comp_def):
        task = asyncio.create_task(
            _nb.post("/dcim/rear-port-templates/", json=comp_def),
            name=comp_def["name"],
        )
        task.add_done_callback(_record_rp_id)
        return task

    await _create_rear_port(nb, dt_obj, dt_def, component)

    # -------------------------------------------------------------------------
    # next create front-ports
    # -------------------------------------------------------------------------

    @creator(label="front-panel")
    def _create_front_panel_ports(_nb, comp_def):
        name = comp_def["name"]
        comp_def["rear_port"] = rear_port_ids[name]
        return asyncio.create_task(
            _nb.post("/dcim/front-port-templates/", json=comp_def), name=name
        )

    await _create_front_panel_ports(nb, dt_obj, dt_def, component)


@creator(label="device-bay")
def create_device_bays(nb, comp_def):
    return asyncio.create_task(
        nb.post("/dcim/device-bay-templates/", json=comp_def), name=comp_def["name"],
    )


async def create_power_outlets(nb, dt_obj, dt_def, component):
    # need the power outlets for cross-references into power outlets

    dt_id = dt_obj["id"]
    res = await nb.get("/dcim/power-port-templates", params={"devicetype_id": dt_id})
    res.raise_for_status()

    power_ports_ids = {rec["name"]: rec["id"] for rec in res.json()["results"]}

    @creator(label="power-outlet")
    def _create(_nb, comp_def):
        comp_def["power_port"] = power_ports_ids[comp_def["power_port"]]
        comp_def["device_type"] = dt_id
        return asyncio.create_task(
            _nb.post("/dcim/power-outlet-templates/", json=comp_def),
            name=comp_def["name"],
        )

    await _create(nb, dt_obj, dt_def, component)


async def ensure_manufacturer(name):
    async with NetboxClient() as nb:
        res = await nb.get("/dcim/manufacturers", params={"name": name})
        res.raise_for_status()
        body = res.json()
        if body["count"]:
            return body["results"][0]

        res = await nb.post(
            "/dcim/manufacturers/", json={"name": name, "slug": name.lower()}
        )
        res.raise_for_status()
        return res.json()


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

    mf_rec = await ensure_manufacturer(dt_def["manufacturer"])
    dt_def["manufacturer"] = mf_rec["id"]
    res = await nb.post("/dcim/device-types/", json=dt_def)
    res.raise_for_status()
    print(f"OK: device-type: {model}")
    return res.json()


async def create_device_type(nb: NetboxClient, dt_def: dict):

    dt_obj = await ensure_device_type(nb, dt_def)

    tasks = list()

    for component, task_creator in COMPONTENTS.items():
        if component in dt_def:
            tasks.append(task_creator(nb, dt_obj, dt_def, component))

    await asyncio.gather(*tasks)


# -----------------------------------------------------------------------------
#
#                                 CLI
#
# -----------------------------------------------------------------------------


@click.command()
@click.option(
    "--file", "files", help="Device-Type YAML file", type=click.File(), multiple=True
)
@click.option("--glob", "glob_", help="Device-Type YAML file-glob pattern")
def cli_load_file(files, glob_):
    nb = NetboxClient()
    loop = asyncio.get_event_loop()

    tasks = list()

    for dt_file in files:
        tasks.append(create_device_type(nb, yaml.safe_load(dt_file)))

    if glob_:
        for file_path in glob(glob_):
            tasks.append(create_device_type(nb, yaml.safe_load(open(file_path))))

    loop.run_until_complete(asyncio.gather(*tasks))

    asyncio.run(nb.aclose())


if __name__ == "__main__":
    cli_load_file()
