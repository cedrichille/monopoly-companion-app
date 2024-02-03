from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from monopoly_companion.db import get_db, next_player, previous_player

bp = Blueprint('gameplay',__name__, static_folder='static')

@bp.route("/", methods=("GET","POST"))
def index():
    db = get_db()
    error = None
    player_dict = session['player_dict']
    current_turn = session['current_turn']
    current_player_id = session['current_player_id']
    current_net_worths = session['net_worths']

    if not session['game_started']:
        error = "Game not started. Please go to Game Setup to begin."
        flash(error)

    if request.method == "POST":
        current_player_order, session['current_turn'] = next_player(player_dict[str(current_player_id)][1], session['no_of_players'], current_turn)
        session['current_player_id'] = list({id for id in player_dict if player_dict[id][1] == current_player_order})[0]

        return redirect(url_for("gameplay.index"))


    return render_template("gameplay/index.html", players=player_dict, current_turn=current_turn, current_player_id=current_player_id, net_worths=current_net_worths)

