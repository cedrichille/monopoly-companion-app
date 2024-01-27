import functools
from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from datetime import datetime
from monopoly_companion.db import get_db

bp = Blueprint('game_setup', __name__, url_prefix='/game-setup')

@bp.route("/")
def home():
    return render_template("home.html")

@bp.route("/hello/")
@bp.route("/hello/<name>")
def hello_there(name = None):
    return render_template(
        "hello_there.html",
        name=name,
        date=datetime.now()
    )

@bp.route("/api/data")
def get_data():
    return bp.send_static_file("data.json")

@bp.route("/about/")
def about():
    return render_template("about.html")

@bp.route("/contact/")
def contact():
    return render_template("contact.html")