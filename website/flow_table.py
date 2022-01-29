import re
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import BlackIp, User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import requests
from requests.auth import HTTPBasicAuth
import json

flow_table = Blueprint('flow_table', __name__)

def getBlockedIps():
    blockedIps = []
    for ip in BlackIp.query.all():
        blockedIps.append(ip.ip)
    return blockedIps

def createnodeDetailList():
    url="http://10.15.3.12:8181/restconf/operational/network-topology:network-topology"
    response = requests.get(url,auth=HTTPBasicAuth('admin', 'admin'))
    data=response.json()
    nodesCount = 0
    nodeDetailsList=[]
    if data and "node" in data["network-topology"]["topology"][2]:
        nodesCount = len(data["network-topology"]["topology"][2]["node"])
        
    count=1
    blockedIps = getBlockedIps()
    for nodeC in range(0,nodesCount):
        if "host" in data["network-topology"]["topology"][2]["node"][nodeC]["node-id"]:
            isBlocked = data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:addresses'][0]['ip'] in blockedIps
            nodeDetailsList.append([count,data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:addresses'][0]['mac'],data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:addresses'][0]['ip'],data["network-topology"]["topology"][2]["node"][nodeC]['host-tracker-service:attachment-points'][0]['active'],isBlocked ])
            count=count+1
    return nodeDetailsList

def createSwitchData():
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
    return switchData

@flow_table.route('/')
def get():
    nodeDetailsList = createnodeDetailList()
    switchData = createSwitchData()
    return render_template("flow_table.html", user=current_user, nodeDetailsList=nodeDetailsList, switchData=switchData)

