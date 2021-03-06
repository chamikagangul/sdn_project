import json
from flask import Blueprint, request, flash
from .models import BlackIp
from . import db
from flask_login import current_user, login_required
import requests
from requests.auth import HTTPBasicAuth
import concurrent.futures
from constant import BASE_IP

blackListAPI = Blueprint('blackListAPI', __name__)

blackListAPI = Blueprint('blackListAPI', __name__)

def load_url(url,dump,switchId,timeout):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, auth=HTTPBasicAuth('admin', 'admin'), data=dump, headers=headers, timeout=timeout)
    return response,switchId

@blackListAPI.route('/block', methods=['GET', 'POST'])
@login_required
def block():
    if request.method == 'POST':
        requestData = json.loads(request.data)

        ip = requestData.get('ip') if requestData else request.form.get(
            'ip')  # "10.0.0.4/32"

        url = f"http://{BASE_IP}:8181/restconf/operations/sal-flow:add-flow"
        data = """{
                    "input": {
                        "node": "/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='openflow:1']",
                        "table_id": 0,
                        "priority":99 ,
                        "match": {
                            "ipv4-destination": "_",
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2048
                                }
                            }
                        },
                        "instructions": {
                            "instruction": [
                                {
                                    "order": 0,
                                    "apply-actions": {
                                        "action": [
                                            {
                                                "order": 0,
                                                "drop-action": {
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }"""
        headers = {
            'Content-Type': 'application/json',
        }
        json_copy = json.loads(data)
        switches = [1, 2, 3, 4, 5, 6, 7]  # need to get from OpenDaylight

        blocksuccess = True


        future_to_url  = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
            for switch in switches:
                json_copy['input']["match"]["ipv4-destination"] = str(ip) + "/32"
                json_copy['input']["node"] = "/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='openflow:" + \
                    str(switch) + "']"
                dump = json.dumps(json_copy)
                future_to_url.append(executor.submit(load_url, url, dump,switch, 5))
                # response = requests.post(url, auth=HTTPBasicAuth(
                #     'admin', 'admin'), data=dump, headers=headers)
                    
                # if response.status_code != 200:
                #     blocksuccess = False
                #     flash('Blocking failed!', category='error')
                # else:
                #     print(f"Blocking success in switch openflow:{switch}")
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    response, switchId= future.result()
                    if response.status_code != 200:
                        blocksuccess = False
                        flash('Blocking failed!', category='error')
                    else:
                        print(f"Blocking success in switch openflow:{switchId}")
                except Exception as exc:
                    blocksuccess = False
                    data = str(type(exc))
                # finally:
                #     print(f"requst completed with : {response.status_code}")
        if blocksuccess:
            new_black_ip = BlackIp(ip=ip, user_id=current_user.id)
            db.session.add(new_black_ip)
            db.session.commit()
            flash('Blocking success!', category='success')
    return "<h1>Blocked</h1>"
    # return render_template("block.html", user=current_user, switches=["openflow:1", "openflow:2", "openflow:3"])


@blackListAPI.route('/unblock', methods=['GET', 'POST'])
@login_required
def unblock():
    if request.method == 'POST':
        requestData = json.loads(request.data)

        ip = requestData.get('ip') if requestData else request.form.get(
            'ip')  # "10.0.0.4/32"

        print(ip)
        # switch = request.form.get('switch')  # "openflow:1"

        url = f"http://{BASE_IP}:8181/restconf/operations/sal-flow:remove-flow"
        data = """{
     "input": {
         "node": "/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='openflow:1']",
         "table_id": 0,
         "priority": 99,
         "strict": true,
         "match": {
             "ipv4-destination": "10.0.0.0/32",
             "ethernet-match": {
                 "ethernet-type": {
                     "type": 2048
                 }
             }
         }
     }
 }"""
        headers = {
            'Content-Type': 'application/json',
        }
        json_copy = json.loads(data)
        switches = [1, 2, 3, 4, 5, 6, 7]  # need to get from OpenDaylight

        future_to_url  = []
        unblockSuccess = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
            for switch in switches:
                json_copy['input']["match"]["ipv4-destination"] = str(ip) + "/32"
                json_copy['input']["node"] = "/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='openflow:" + \
                    str(switch) + "']"
                dump = json.dumps(json_copy)

                future_to_url.append(executor.submit(load_url, url, dump,switch, 5))
                
                # if response.status_code != 200:
                #     flash('unblocking failed!', category='error')
                # else:
                #     print(f"Unblocking success in switch openflow:{switch}")
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    response, switchId= future.result()
                    if response.status_code != 200:
                        unblockSuccess = False
                        flash('Unblocking failed!', category='error')
                    else:
                        print(f"Unblocking success in switch openflow:{switchId}")
                except Exception as exc:
                    unblockSuccess = False
                    data = str(type(exc))

            if unblockSuccess:
                # remove ip from database
                db.session.query(BlackIp).filter(BlackIp.ip == ip).delete()
                db.session.commit()
                flash('unblocking success!', category='success')
    return "<h1>Unblocked</h1>"
