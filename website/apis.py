from flask import Blueprint, request ,render_template, flash, jsonify
from flask_login import login_required, current_user
import json
import requests
from requests.auth import HTTPBasicAuth

apis = Blueprint('apis', __name__)


@apis.route('/show_data', methods=['GET', 'POST'])
@login_required
def showData():
    url="http://10.15.3.10:8181/restconf/operational/network-topology:network-topology"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data=response.json()
    if data:
        nodesCount = len(data["network-topology"]["topology"][0]["node"])
        nodeDetailsList=[]
    count=1
    for nodeC in range(0,nodesCount):
        if "host" in data["network-topology"]["topology"][0]["node"][nodeC]["node-id"]:
            nodeDetailsList.append([count,data["network-topology"]["topology"][0]["node"][nodeC]['host-tracker-service:addresses'][0]['mac'],data["network-topology"]["topology"][0]["node"][nodeC]['host-tracker-service:addresses'][0]['ip'],data["network-topology"]["topology"][0]["node"][nodeC]['host-tracker-service:attachment-points'][0]['active']])
            count=count+1

    url="http://10.15.3.10:8181/restconf/operational/opendaylight-inventory:nodes"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data2=response.json()
    if data2:
        switchData=[]
        nodesCount = len(data2["nodes"]["node"])
        for switch in range(0,nodesCount):
            for i in data2["nodes"]["node"][switch]["flow-node-inventory:table"]:
                if i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"] != 0:
                    switchData.append([data2["nodes"]["node"][switch]["id"],i["id"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-looked-up"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-matched"]])

    return render_template("scj_page.html", user=current_user, nodeData = nodeDetailsList,switchData=switchData)



