from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import BlackIp, User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import requests
from requests.auth import HTTPBasicAuth
import json

apis = Blueprint('apis', __name__)


@apis.route('/flow_table')
def flow_table():
    url="http://10.15.3.12:8181/restconf/operational/network-topology:network-topology"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data=response.json()
    nodesCount = 0
    nodeDetailsList=[]
    if data and "node" in data["network-topology"]["topology"][2]:
        nodesCount = len(data["network-topology"]["topology"][2]["node"])
        
    count=1
    for nodeC in range(0,nodesCount):
        if "host" in data["network-topology"]["topology"][2]["node"][nodeC]["node-id"]:
            nodeDetailsList.append([count,data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:addresses'][0]['mac'],data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:addresses'][0]['ip'],data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:attachment-points'][0]['active']])
            count=count+1

    url="http://10.15.3.12:8181/restconf/operational/opendaylight-inventory:nodes"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data2=response.json()
    if data2:
        switchData=[]
        nodesCount = len(data2["nodes"]["node"])
        for switch in range(0,nodesCount):
            for i in data2["nodes"]["node"][switch]["flow-node-inventory:table"]:
                if i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"] != 0:
                    flows = []
                    for f in i["flow"]:
                        flows.append({'id' : f["id"], 'priority': f.get("priority",None),'instructions' :  f.get("instructions",None)})
                        
                    switchData.append([data2["nodes"]["node"][switch]["id"],i["id"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-looked-up"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-matched"], flows])
   
    return render_template("flow_table.html", user=current_user, nodeDetailsList=nodeDetailsList, switchData=switchData)
@apis.route('/test')


# @apis.route('/block', methods=['GET', 'POST'])
# @login_required
def block():
    if request.method == 'POST':
        requestData = json.loads(request.data)

        ip =  requestData.get('ip') if requestData else request.form.get('ip')  # "10.0.0.4/32"

        print(ip)

        switch = request.form.get('switch')  # "openflow:1"
        url = "http://10.15.3.12:8181/restconf/operations/sal-flow:add-flow"
        dataXml = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <input xmlns="urn:opendaylight:flow:service">
                <node xmlns:inv="urn:opendaylight:inventory">/inv:nodes/inv:node[inv:id={switch}]</node>
                <table_id>0</table_id>
                <cookie>3</cookie>
                <priority>99</priority>
                <match>
                    <ethernet-match>
                        <ethernet-type>
                            <type>2048</type>
                        </ethernet-type>
                    </ethernet-match>
                    <ipv4-destination>{ip}</ipv4-destination>
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
        response = requests.post(url, auth=HTTPBasicAuth(
            'admin', 'admin'), data=dataXml)

        if response.status_code == 200:
            flash('Blocking success!', category='success')
            # save to database
            new_black_ip = BlackIp(ip=ip, switch=switch, user_id=current_user.id)
            db.session.add(new_black_ip)
            db.session.commit()
        else:
            flash('Blocking failed!', category='error')
    return ""
    # return render_template("home.html", user=current_user)
