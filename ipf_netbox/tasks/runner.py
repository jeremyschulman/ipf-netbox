from invoke import Config, Program

from ipf_netbox.tasks.root import root

program = Program(namespace=root)


def run(argv):
    argv = list(argv)

    if '-p' not in argv:
        argv.insert(0, '-p')

    class _Config(Config):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self["private"] = {"name": "Jeremy"}

    program.config_class = _Config
    program.run(argv, exit=False)
