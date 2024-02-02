from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
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
                "SELECT rowid,* FROM game_version WHERE game_version_name = ?",
                (game_version_name,)
            ).fetchone()

        if game_version is None:
            error = 'Game version not found'
        else:
            session.clear()
            session['game_version_id'] = game_version['rowid']
            session['no_of_players'] = no_of_players
            
            init_property_ownership(game_version['rowid'])

            return redirect(url_for('game_setup.player_registration'))

        flash(error)

    return render_template("game_setup/index.html")

@bp.route("/player_registration/", methods=("GET","POST"))
def player_registration():
    no_of_players = session['no_of_players']
    player_names = []

    if request.method == "POST":
        db = get_db()
        error = None

        for player in range(1, no_of_players+1):
            player_name = request.form['player_' + str(player) + '_name'] 

            if not player_name:
                error = "Player " + str(player) + " name required"
                flash(error)
            else:
                player_names.append(player_name)
        
        if error is None:
            for player in player_names:
                db.execute(
                    "INSERT INTO players(player_name, player_order) VALUES (?, ?)",
                    (player, player_names.index(player)+1)
                )
            db.commit()

            # Need to do net worth dictionary calc and sql insert here and make it available to gameplay.py and gameplay.index.html
            player_net_worths = {}

            for player in player_names:
                # get net worth figure. 
                net_worth = db.execute(
                    "SELECT net_worth FROM net_worth WHERE player_id = ?",
                    (player_names.index(player),)
                )
                if not net_worth:
                    error = "net_worth table didn't find player"
                else:
                    player_net_worths[player] = net_worth
            session['player_names'] = player_names
            session['game_started'] = 1
            session['net_worths'] = player_net_worths        

            return redirect(url_for("gameplay.index"),player_names=player_names, player_net_worths=player_net_worths)
        
    return render_template(
        "game_setup/player_registration.html",no_of_players=no_of_players
    )
