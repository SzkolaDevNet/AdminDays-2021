
# -*- coding: utf-8 -*-
# (c) 2021 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json, re, random, requests, urllib3
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException


def print_response(resp):
    print(json.dumps(json.loads(resp), indent=2))


def split_ifname(ifname):
    regexp = re.compile('([a-zA-Z]+)([0-9]+)')
    return regexp.match(ifname).groups()


def restconf_get_interface_info(ip, ifname):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    iface = split_ifname(ifname)

    if len(iface) != 2:
        return

    restconf_headers = {'Accept': 'application/yang-data+json'}
    restconf_base = 'https://' + ip + '/restconf/data'
    auth = ('cisco', 'cisco')
    url = restconf_base + '/Cisco-IOS-XE-native:native/interface/' + iface[0] + '=' + iface[1]

    try:
        response = requests.get(url=url, auth=auth, headers=restconf_headers, verify=False)
        if response.status_code == 200:
            print_response(response.content)
        else:
            print(str(response.status_code) + ": " + response.reason)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def restconf_change_loopback_ip(ip, ifname):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    iface = split_ifname(ifname)

    if len(iface) != 2:
        return

    restconf_headers = {'Accept': 'application/yang-data+json',
                        'Content-Type': 'application/yang-data+json'}
    restconf_base = 'https://' + ip + '/restconf/data'
    auth = ('cisco', 'cisco')
    url = restconf_base + '/Cisco-IOS-XE-native:native/interface/' + iface[0] + '=' + iface[1]

    data = json.dumps({
        "Cisco-IOS-XE-native:Loopback": {
            "ip": {
                "address": {
                    "primary": {
                        "address": "10.100.0." + str(random.randint(1, 254)),
                        "mask": "255.255.255.255"
                    }
                }
            }
        }
    })

    try:
        response = requests.patch(url=url, auth=auth, headers=restconf_headers, data=data, verify=False)
        if response.status_code == 204:
            print('Response Code: ' + str(response.status_code))
        else:
            print(str(response.status_code) + ": " + response.reason)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def netmiko_get_interface_info(ip, ifname):
    device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': 'cisco',
        'password': 'cisco',
    }

    try:
        netmiko_connect = ConnectHandler(**device)
        cmd = 'show running-config interface ' + ifname
        print(netmiko_connect.send_command(cmd))
    except NetmikoAuthenticationException or NetmikoTimeoutException as e:
        raise SystemExit(e)


def netmiko_change_loopback_ip(ip, ifname):
    device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': 'cisco',
        'password': 'cisco',
    }

    try:
        netmiko_connect = ConnectHandler(**device)

        commands = ['interface ' + ifname,
                    'ip address 10.100.0.' + str(random.randint(1, 254)) + ' 255.255.255.255']
        result = netmiko_connect.send_config_set(commands)
        print(result)
    except NetmikoAuthenticationException or NetmikoTimeoutException as e:
        raise SystemExit(e)


def check_if_restconf(ip):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    restconf_headers = {'Accept': 'application/yang-data+json'}
    restconf_base = 'https://' + ip + '/restconf/data'
    auth = ('cisco', 'cisco')
    url = restconf_base + '/Cisco-IOS-XE-native:native/hostname/'

    try:
        response = requests.get(url=url, auth=auth, headers=restconf_headers, verify=False)
    except requests.exceptions.RequestException:
        return False

    if response.status_code == 200:
        return True
    else:
        return False


if __name__ == '__main__':
    host = "172.16.1.51"
    interface = "Loopback100"

    if check_if_restconf(host):
        print("Using RESTCONF")
        restconf_get_interface_info(host, interface)
        restconf_change_loopback_ip(host, interface)
    else:
        print("Unisng Netmiko")
        netmiko_get_interface_info(host, interface)
        netmiko_change_loopback_ip(host, interface)
