import requests
import urllib3
import configparser
from requests.auth import HTTPBasicAuth
from constant import BASE_IP

# url="http://10.15.3.10:8181/restconf/operational/network-topology:network-topology"
# response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))

url = f"http://{BASE_IP}:8181/restconf/operations/sal-flow:add-flow"


dataXml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<input xmlns="urn:opendaylight:flow:service">
    <node xmlns:inv="urn:opendaylight:inventory">/inv:nodes/inv:node[inv:id="openflow:1"]</node>
    <table_id>0</table_id>
    <cookie>3</cookie>
    <priority>99</priority>
    <match>
        <ethernet-match>
            <ethernet-type>
                <type>2048</type>
            </ethernet-type>
        </ethernet-match>
        <ipv4-destination>10.0.0.4/32</ipv4-destination>
    </match>
    <instructions>
        <instruction>
            <order>0</order>
            <apply-actions>
                <action>
                    <order>0</order>
                    <drop-action/>
                </action>
            </apply-actions>
        </instruction>
    </instructions>
</input>"""
headers = {'Content-Type': 'application/xml'}
response = requests.post(url,auth=HTTPBasicAuth('admin', 'admin'), data=dataXml,headers=headers)
print (response)
print (response.text)

