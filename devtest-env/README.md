# Dev-Test Envionrment

This directory contains the necessary artifacts used to create a develop-test enviornment that
includes a docker based Netbox system.

## Create a Netbox Docker envioronment.

Follow [this
blog](https://www.techrepublic.com/article/how-to-deploy-the-netbox-network-documentationmanagement-tool-with-docker/)
to stand up a netbox enviornment using Docker.

If you want to run a specific version of Netbox, ensure that you export the variable `VERSION`
before you perform the `docker-compose up` commmand.  For example, if you want to run
Netbox version 2.8.5, you would do the following:

```shell script
VERSION=v2.8.5 docker-compose up -d
```

I have also found that when running ealier releases, for example v2.8.5, that I needed
to update the docker-compose.yml file to comment out some of the mount-points; otherwise
I would observe an nginx bad-gateway (502).  For example, note the commentted out lines:

```yaml
  netbox: &netbox
    image: netboxcommunity/netbox:${VERSION-latest}
    depends_on:
    - postgres
    - redis
    - redis-cache
    - netbox-worker
    env_file: env/netbox.env
    user: '101'
    volumes:
#    - ./startup_scripts:/opt/netbox/startup_scripts:z,ro
#    - ./initializers:/opt/netbox/initializers:z,ro
#    - ./configuration:/etc/netbox/config:z,ro
    - ./reports:/etc/netbox/reports:z,ro
    - ./scripts:/etc/netbox/scripts:z,ro
    - netbox-nginx-config:/etc/netbox-nginx:z
    - netbox-static-files:/opt/netbox/netbox/static:z
    - netbox-media-files:/opt/netbox/netbox/media:z
```
