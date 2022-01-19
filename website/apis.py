from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


apis = Blueprint('auth', __name__)


@apis.route('/test')
@login_required
def testAPI():
    return "This is a test API."
