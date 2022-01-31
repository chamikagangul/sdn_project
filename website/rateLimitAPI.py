from dbm import dumb
import json
from typing import Dict
from flask import Blueprint, redirect, render_template, request, flash, url_for
from sqlalchemy import true
from .models import RateIp
from . import db
from flask_login import current_user, login_required
import requests
from requests.auth import HTTPBasicAuth
import concurrent.futures

rateLimitAPI = Blueprint('rateLimitAPI', __name__)

def findSwitch(ip):
    url="http://10.15.3.12:8181/restconf/operational/opendaylight-inventory:nodes"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data=response.json()
    if data:
        nodesCount = len(data["nodes"]["node"])
        for switch in range(0,nodesCount):
            for node in data["nodes"]["node"][switch]["node-connector"]:
                if "address-tracker:addresses" in node:
                    if node["address-tracker:addresses"][0]["ip"] == ip:
                        return node["flow-node-inventory:port-number"], data["nodes"]["node"][switch]["id"]
    return None, None
    
def load_url(url, dump, timeout):
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, auth=HTTPBasicAuth('admin', 'admin'), data=dump, headers=headers)
    return response

@rateLimitAPI.route('/reduce/', methods=['GET', 'POST'])
@login_required
def reduce():
    if request.method == 'POST':
        # requestData = json.loads(request.data)
        # ip =  request.form.get('ip')
        ip = request.args.get('ip') #getting from params
        rate =  request.form.get('rate') #getting from form

        print("POST : ",ip,rate)
        node_connector, switchID = findSwitch(ip)
        url1 = "http://10.15.3.12:8181/restconf/config/opendaylight-inventory:nodes/node/" + str(switchID) + "/meter/" + str(node_connector)
        # url1 = "http://10.15.3.12:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:3/meter/1"
        data1 = """{"flow-node-inventory:meter": [
                {
                    "meter-id": 1,
                    "meter-band-headers": {
                        "meter-band-header": [
                            {
                                "band-id": 0,
                                "drop-rate": 100000,
                                "drop-burst-size": 100000,
                                "meter-band-types": {
                                    "flags": "ofpmbt-drop"
                                }
                            }
                        ]
                    },
                    "flags": "meter-kbps",
                    "meter-name": "Foo"
                }
            ]
        }"""

        dump1_temp = json.loads(data1)
        dump1_temp["flow-node-inventory:meter"][0]["meter-id"] = node_connector
        dump1_temp["flow-node-inventory:meter"][0]["meter-band-headers"]["meter-band-header"][0]["drop-burst-size"] = str(rate)
        dump1_temp["flow-node-inventory:meter"][0]["meter-band-headers"]["meter-band-header"][0]["drop-rate"] = str(rate)
        dump1 = json.dumps(dump1_temp)
        response1 = load_url(url1, dump1, 5)
        print(f"meter response code : {response1.status_code}")
        print(f"Added meter to switch openflow: {switchID}")

        url2 = "http://10.15.3.12:8181/restconf/config/opendaylight-inventory:nodes/node/" + str(switchID) + "/table/0/flow/L2_Rule_h_to_h" + ip

        data2 = """{
            "flow-node-inventory:flow": [
                {
                    "id": "L2_Rule_h_to_h",
                    "priority": 99,
                    "table_id": 0,
                    "hard-timeout": 0,
                    "match": {
                        "ethernet-match": {
                            "ethernet-type": {
                                "type": 2048
                            }
                        },
                        "ipv4-destination": "10.0.0.0/32",
                        "ipv4-source": "10.0.0.0/8"
                    },
                    "flow-name": "L2_Rule_h_to_h",
                    "instructions": {
                        "instruction": [
                            {
                                "order": 0,
                                "meter": {
                                    "meter-id": 1
                                }
                            },
                            {
                                "order": 1,
                                "apply-actions": {
                                    "action": [
                                        {
                                            "order": 1,
                                            "output-action": {
                                                "max-length": 65535,
                                                "output-node-connector": "1"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    "idle-timeout": 0,
                    "barrier": true
                }
            ]
        }"""

        dump2_temp = json.loads(data2)
        dump2_temp['flow-node-inventory:flow'][0]["match"]["ipv4-destination"] = str(ip) + "/32"
        dump2_temp['flow-node-inventory:flow'][0]["instructions"]["instruction"][1]["apply-actions"]["action"][0]["output-action"]["output-node-connector"] = node_connector
        dump2_temp['flow-node-inventory:flow'][0]["instructions"]["instruction"][0]["meter"]["meter-id"] = node_connector


        dump2_temp["flow-node-inventory:flow"][0]["id"] = "L2_Rule_h_to_h" + ip
        dump2_temp["flow-node-inventory:flow"][0]["flow-name"] = "L2_Rule_h_to_h" + ip

        dump2 = json.dumps(dump2_temp)
        response2 = load_url(url2, dump2, 5)

        print(f"entry response code : {response2.status_code}")

        if response1.status_code == 201:
            flash('rate limiting success!', category='success')
            print(f"Added flow entry to switch openflow: {switchID}")
            new_rate_ip = RateIp(ip=ip, rateLimit = 100000, user_id=current_user.id)
            db.session.add(new_rate_ip)
            db.session.commit()
        elif response1.status_code == 200:
            flash('rate limiting success!', category='success')
            print(f"Updated flow entry to switch openflow: {switchID}")
            RateIp.query.filter_by(ip=ip).update(dict(rateLimit=90000))
            # new_rate_ip = RateIp(ip=ip, rateLimit = 100000, user_id=current_user.id)
            # db.session.update(new_rate_ip)
            db.session.commit()
        else:
            flash('cannot limit the rate!', category='error')
        return redirect(url_for('flow_table.get'))
    elif request.method == 'GET':
        return render_template("rate_limit.html", user=current_user, ip = request.args.get('ip'))

@rateLimitAPI.route('/reset', methods=['GET', 'POST'])
# @login_required
def reset():
    if request.method == 'POST':
        requestData = json.loads(request.data)

        ip = requestData.get('ip') if requestData else request.form.get(
            'ip')  # "10.0.0.4/32"
        _, switchID = findSwitch(ip)
        url = "http://10.15.3.12:8181/restconf/config/opendaylight-inventory:nodes/node/" + str(switchID) + "/meter/1"
        data = """{"flow-node-inventory:meter": [
                {
                    "meter-id": 1,
                    "meter-band-headers": {
                        "meter-band-header": [
                            {
                                "band-id": 0,
                                "drop-rate": 100000,
                                "drop-burst-size": 100000,
                                "meter-band-types": {
                                    "flags": "ofpmbt-drop"
                                }
                            }
                        ]
                    },
                    "flags": "meter-kbps",
                    "meter-name": "Foo"
                }
            ]
        }"""

        dump_temp = json.loads(data)
        dump = json.dumps(dump_temp)
        headers = {'Content-Type': 'application/json'}
        response = requests.delete(url, auth=HTTPBasicAuth('admin', 'admin'), data=dump, headers=headers)
        print(f"meter response code : {response.status_code}")
        print(f"deleted meter to switch openflow: {switchID}")

    # return render_template("block.html", user=current_user, switches=["openflow:1", "openflow:2", "openflow:3"])
