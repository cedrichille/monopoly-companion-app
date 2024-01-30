import functools
from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from datetime import datetime
from monopoly_companion.db import get_db, init_property_ownership

bp = Blueprint('game_setup', __name__, url_prefix='/game-setup', static_folder='static')

# this blueprint contains the code for game version selection and player registration.

@bp.route("/", methods=("GET","POST"))
def index():
    if request.method == "POST":
        game_version_name = request.form['game_version']
        no_of_players = int(request.form['no_of_players'])
        db = get_db()
        error = None
        
        if not game_version_name:
            error = 'Game version is required.'
        elif not no_of_players:
            error = 'Number of players is required.'

        if error is None:
            game_version = db.execute(
                "SELECT * FROM game_version WHERE game_version_name = ?",
                (game_version_name,)
            ).fetchone()

        if game_version is None:
            error = 'Game version not found'
        else:
            session.clear()
            session['game_version_id'] = game_version['game_version_id']
            session['no_of_players'] = no_of_players
            
            init_property_ownership(game_version['game_version_id'])

            return redirect(url_for('game_setup.player_registration'))

        flash(error)

    return render_template("game_setup/index.html")

@bp.route("/player_registration/", methods=("GET","POST"))
def player_registration(name = None):
    no_of_players = session['no_of_players']
    


    return render_template(
        "game_setup/player_registration.html",no_of_players=no_of_players
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