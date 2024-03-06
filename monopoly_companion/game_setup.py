from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from monopoly_companion.db import get_db, init_property_ownership, init_special_counter, starting_cash, get_property_value, get_net_worth, log_net_worth

bp = Blueprint('game_setup', __name__, url_prefix='/game-setup', static_folder='static')

# this blueprint contains the code for game version selection and player registration.

@bp.route("/", methods=("GET","POST"))
def index():
    db = get_db()
    if request.method == "GET":
        game_versions = db.execute(
            "SELECT * FROM game_version"
        ).fetchall()

        game_version_names = []

        for game_version in game_versions:
            game_version_names.append(game_version['game_version_name'])
        
        session['game_version_names'] = game_version_names

    elif request.method == "POST":
        game_version_name = request.form['game_version']
        no_of_players = int(request.form['no_of_players'])
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
            session['go_value'] = game_version['go_value']
            session['no_of_players'] = no_of_players

            if request.form.get('double_go'):
                session['double_go'] = True
            else:
                session['double_go'] = False

            init_property_ownership(db, session['game_version_id'])

            return redirect(url_for('game_setup.player_registration'))

        flash(error)

    return render_template("game_setup/index.html",game_version_names=session['game_version_names'])

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
                player_dict[int(player_names.index(player)+3)] = [player, player_names.index(player)+1]

            total_cash, starting_cash_per_player = db.execute(
                "SELECT total_cash, starting_cash_balance FROM game_version where rowid = ?",
                (session['game_version_id'],)
            ).fetchone()

            player_starting_cash = starting_cash(no_of_players, player_names, total_cash, starting_cash_per_player)

            property_values = get_property_value(db, player_names)

            player_names_incl_static = ["Bank", "Free Parking"] + player_names

            for player in player_names_incl_static:
                player_id = player_names_incl_static.index(player)+1
                cash_balance = player_starting_cash[player_id][1]
                net_property_value = property_values[player_id][3]
                gross_property_value = property_values[player_id][4]
                improvement_value = property_values[player_id][5]
                db.execute(
                    """
                    INSERT INTO net_worth (turn, player_id, cash_balance, net_property_value, improvement_value, gross_property_value) 
                    VALUES (0, ?, ?, ?, ?, ?)
                    """,
                    (player_id, cash_balance, net_property_value, improvement_value, gross_property_value)
                )
                init_special_counter(db, player_id)

            log_net_worth(db)
            db.commit()

            current_net_worth_table, current_net_worths = get_net_worth(db)

            session['player_dict'] = player_dict
            session['current_player_id'] = 3
            session['game_started'] = 1
            session['current_turn'] = 1

            return redirect(url_for("gameplay.index"))
  
    return render_template(
        "game_setup/player_registration.html",no_of_players=no_of_players
    )
