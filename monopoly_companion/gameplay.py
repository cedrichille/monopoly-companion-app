from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from monopoly_companion.db import get_db

bp = Blueprint('gameplay',__name__, static_folder='static')

@bp.route("/", methods=("GET","POST"))
def index():
    if session['game_started'] == 1:
        current_turn = session['current_turn']
        current_player = session['current_player']
        current_player_order = session['current_player_order']
    else:
        current_turn = 1
        current_player = session['player_names'][0]
        current_player_order = 1
    
    db = get_db()
    error = None
    

    
    if request.method == "POST":
        print("hello")

    return render_template ("gameplay/index.html", player_names=session['player_names'], player_net_worths=session['player_net_worths'])

