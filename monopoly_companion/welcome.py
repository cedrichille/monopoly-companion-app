import functools
from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from datetime import datetime
from monopoly_companion.db import get_db, init_data

bp = Blueprint('welcome',__name__,url_prefix='/welcome')

@bp.route("/", methods=("GET","POST"))
def index(): 
    if request.method == "POST":
        init_data()
        return redirect(url_for("game_setup.index"))
    else:
        return render_template("welcome/index.html")

