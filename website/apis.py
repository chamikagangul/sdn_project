from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import requests
from requests.auth import HTTPBasicAuth

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
                    switchData.append([data2["nodes"]["node"][switch]["id"],i["id"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-looked-up"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-matched"]])
    print(nodeDetailsList,switchData)
    return render_template("flow_table.html", user=current_user)