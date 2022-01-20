from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


apis = Blueprint('apis', __name__)


@apis.route('/test')
def testAPI():
    return "This is a test API."
