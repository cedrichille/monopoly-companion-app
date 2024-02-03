from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from monopoly_companion.db import get_db

bp = Blueprint('gameplay',__name__, static_folder='static')

@bp.route("/", methods=("GET","POST"))
def index():
    db = get_db()
    error = None

    if not session['game_started']:
        error = "Game not started. Please go to Game Setup to begin."
    else:
        player_dict = session['player_dict']
        current_turn = session['current_turn']
        current_player = session['current_player']
        current_net_worths = session['net_worths']



    
        if request.method == "POST":
            print("hello")

    return render_template ("gameplay/index.html", players=player_dict, current_turn=current_turn, current_player=current_player, net_worths=current_net_worths)

