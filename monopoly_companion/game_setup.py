from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from monopoly_companion.db import get_db, init_property_ownership, starting_cash, get_property_value, get_net_worth

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
            
            init_property_ownership(db, game_version['rowid'])

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
            player_dict = {}
            for player in player_names:
                db.execute(
                    "INSERT INTO players(player_name, player_order) VALUES (?, ?)",
                    (player, player_names.index(player)+1)
                )

                player_dict[player_names.index(player)+3] = [player, player_names.index(player)+1]

            # Need to do net worth dictionary calc and sql insert here and make it available to gameplay.py and gameplay.index.html
            total_cash, starting_cash_per_player = db.execute(
                "SELECT total_cash, starting_cash_balance FROM game_version where rowid = ?",
                (session['game_version_id'],)
            ).fetchone()

            player_starting_cash = starting_cash(db, no_of_players, player_names, total_cash, starting_cash_per_player)

            property_values = get_property_value(db, player_names)

            player_names_incl_static = ["Bank", "Free Parking"] + player_names

            for player in player_names_incl_static:
                player_id = player_names_incl_static.index(player)+1
                cash_balance = player_starting_cash[player_id][1]
                net_property_value = property_values[player_id][3]
                gross_property_value = property_values[player_id][4]
                improvement_value = property_values[player_id][5]
                net_worth = cash_balance + improvement_value + net_property_value
                db.execute(
                    """
                    INSERT INTO net_worth (turn, player_id, cash_balance, net_property_value, improvement_value, gross_property_value, net_worth) 
                    VALUES (1, ?, ?, ?, ?, ?, ?)
                    """,
                    (player_id, cash_balance, net_property_value, improvement_value, gross_property_value, net_worth)
                )

            db.commit()

            current_net_worth_table, current_net_worths = get_net_worth(db)

            session['player_dict'] = player_dict
            session['current_player'] = player_dict[3]
            session['game_started'] = 1
            session['current_turn'] = 1
            session['net_worths'] = current_net_worths

            return redirect(url_for("gameplay.index"))
  
    return render_template(
        "game_setup/player_registration.html",no_of_players=no_of_players
    )
