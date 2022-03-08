from constant import BASE_IP
from flask import Blueprint, render_template
from flask_login import login_required, current_user
import requests
from requests.auth import HTTPBasicAuth

switches = Blueprint('switches', __name__)

def createSwitchData():
    url=f"http://{BASE_IP}:8181/restconf/operational/opendaylight-inventory:nodes"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data2=response.json()
    if data2:
        switchData=[]
        if "node" in data2["nodes"]:
            nodesCount = len(data2["nodes"]["node"])
        else:
            nodesCount = 0
        for switch in range(0,nodesCount):
            for i in data2["nodes"]["node"][switch]["flow-node-inventory:table"]:
                if i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"] != 0:
                    flows = []
                    for f in i["flow"]:
                        flows.append({'id' : f["id"], 'priority': f.get("priority",None),'instructions' :  f.get("instructions",None)})
                        
                    switchData.append([data2["nodes"]["node"][switch]["id"],i["id"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["active-flows"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-looked-up"],i["opendaylight-flow-table-statistics:flow-table-statistics"]["packets-matched"], flows])
    return switchData
@switches.route('/')
@login_required
def renderSwitches():
    switchData = createSwitchData()
    return render_template("switches.html", user=current_user, switchData=switchData)