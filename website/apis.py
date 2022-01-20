from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import BlackIp, User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import requests
from requests.auth import HTTPBasicAuth

apis = Blueprint('apis', __name__)


@apis.route('/test')
def testAPI():
    return "This is a test API."


@apis.route('/block', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ip = request.form.get('ip')  # "10.0.0.4/32"
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

    return render_template("home.html", user=current_user)
