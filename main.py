import os
import docker
import CloudFlare
from datetime import datetime


def point_domain(name):
    try:
        r = cf.zones.dns_records.post(zone_id,
                                      data={'type': 'CNAME', 'name': name, 'content': target_domain, 'ttl': ttl,
                                            'proxied': proxied})

    except CloudFlare.exceptions.CloudFlareAPIError as e:
        print('/zones.dns_records.post %s - %d %s' % (name, e, e))


def check_container(c):
    for prop in c.attrs.get('Config').get('Env'):
        if 'VIRTUAL_HOST' in prop or 'FLARE_DOMAIN' in prop:
            value = prop.split("=")[1].strip()
            if ',' in value:
                for v in value.split(","):
                    point_domain(v)
            else:
                point_domain(value)


def init():
    for c in client.containers.list(all=True):
        check_container(c)


try:
    zone_id = os.environ['ZONE_ID']
except KeyError as e:
    exit('ZONE_ID not defined')

try:
    email = os.environ['EMAIL']
except KeyError as e:
    exit('EMAIL not defined')

try:
    token = os.environ['TOKEN']
except KeyError as e:
    exit('TOKEN not defined')

try:
    target_domain = os.environ['TARGET_DOMAIN']
except KeyError as e:
    exit('TARGET_DOMAIN not defined')

proxied = True if os.environ.get('PROXIED') == 'True' or True else False

try:
    ttl = os.environ['TTL']
except KeyError as e:
    ttl = 120

cf = CloudFlare.CloudFlare(email=email, token=token)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

init()

t = datetime.now().time().strftime("%s")

for event in client.events(since=t, filters={'status': 'start'}, decode=True):
    if event.get('status') == 'start':
        try:
            print('started %s' % event.get('id'))
            check_container(client.containers.get(event.get('id')))
        except docker.errors.NotFound as e:
            print('Ignoring %s' % event.get('from'))
