#!/usr/local/bin/python
import os
import requests
import yaml
import socket
import time
from pythonping import ping
from yaml.loader import SafeLoader
from kubernetes import client, config

def Pingable(hostname, waittime=1000):
    '''Function returns True if host IP returns a ping, else False'''
    assert isinstance(hostname, str), \
        "IP/hostname must be provided as a string."
    result = ping(hostname)
    print(result)
    return result.success()

def Resolvable(hostname):
    '''Function returns true if hostname can be resolved to an IP with default DNS server'''
    assert isinstance(hostname, str), \
        "IP/hostname must be provided as a string."
    try:
        data = socket.gethostbyname(hostname)
        ip = repr(data)
        if ip:
            print('hostname: {} resolves to IP {}.'.format(hostname, ip))
            Resolvable = True
    except Exception:
        print('hostname: {} can not be resolved.'.format(hostname))
        Resolvable = False
    return Resolvable

def Accessible(URL):
    '''Function returns True if URL is accessible, else False'''
    assert isinstance(URL, str), \
        "URL must be provided as a string."
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            URL_UP = True
    except requests.exceptions.SSLError:
        print('Warning: SSLCertVerificationError for URL: {}'.format(URL))
        URL_UP = True
    except:
        URL_UP = False
    return URL_UP

def GetConfig(config_path):
    '''Reads YAML configuration and returns as Dictionary/List'''
    assert isinstance(config_path, str), \
        "config_path must be provided as a string."
    if os.path.isfile(config_path):
        with open(config_path) as f:
            data = yaml.load(f, Loader=SafeLoader)
    return data

def SendTelegram(msg, token, group_id):
    '''Sends message to telegram group'''
    assert isinstance(msg, str), \
        "msg must be provided as a string."
    assert isinstance(token, str), \
        "token must be provided as a string."
    assert isinstance(group_id, str), \
        "group_id must be provided as a string."
    to_url = 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}&parse_mode=HTML'.format(token, group_id, msg)
    resp = requests.get(to_url)
    print(resp.text)

def SendTelegramAll(msg, token, group_ids):
    '''Sends message to all telegram groups'''
    assert isinstance(msg, str), \
        "msg must be provided as a string."
    assert isinstance(token, str), \
        "token must be provided as a string."
    assert isinstance(group_ids, list), \
        "group_ids must be provided as a list."
    for group_id in group_ids:
        SendTelegram(msg=msg, token=token, group_id=group_id)

def APIServerUp():
    '''Check if Kubernetes API Server is up from inside the cluster'''
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        apis = len(v1.get_api_resources().to_dict()['resources'])
        if apis > 0:
            Cluster_Live = True
    except:
        Cluster_Live = False
    return Cluster_Live

if __name__ == "__main__":
    configuration = GetConfig('/etc/config/monitor-config.yaml')
    id = configuration['id']
    telegram_token = configuration['telegram_config']['token']
    telegram_group_ids = configuration['telegram_config']['group_ids']
    resolve_hosts = configuration['monitor']['resolve']
    ping_hosts = configuration['monitor']['ping']
    access_urls = configuration['monitor']['access']
    check_kube_api = configuration['monitor']['check_kube_api']

    while True:

        if check_kube_api:
            if not APIServerUp():
                msg = '{}: API Server unreachable from inside the cluster.'.format(id)
                print(msg)
                SendTelegramAll(msg=msg, token=telegram_token, group_ids=telegram_group_ids)

        if resolve_hosts:
            for hostname in resolve_hosts:
                if not Resolvable(hostname):
                    msg = 'Hostname: {} could not be resolved from inside the cluster.'.format(hostname)
                    print(msg)
                    SendTelegramAll(msg=msg, token=telegram_token, group_ids=telegram_group_ids)

        if ping_hosts:
            for hostname in ping_hosts:
                if not Pingable(hostname):
                    msg = 'Hostname: {} is not pingable from inside the cluster.'.format(hostname)
                    print(msg)
                    SendTelegramAll(msg=msg, token=telegram_token, group_ids=telegram_group_ids)

        if access_urls:
            for url in access_urls:
                if not Accessible(url):
                    msg: 'URL: {} is not accessible from inside the cluster.'.format(url)
                    print(msg)
                    SendTelegramAll(msg=msg, token=telegram_token, group_ids=telegram_group_ids)

        time.sleep(600)

