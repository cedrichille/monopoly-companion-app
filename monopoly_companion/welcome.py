from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from monopoly_companion.db import init_data, get_db

bp = Blueprint('welcome',__name__,url_prefix='/welcome')

@bp.route("/", methods=("GET","POST"))
def index(): 
    if request.method == "POST":
        db = get_db()
        init_data(db)
                
        session['game_started'] = 0

        return redirect(url_for("game_setup.index"))
    else:
        return render_template("welcome/index.html")

