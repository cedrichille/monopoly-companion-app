from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from monopoly_companion.db import get_db, next_player, previous_player, purchase_property, get_net_worth, go, update_net_worth_turn, purchase_property, rent

bp = Blueprint('gameplay',__name__, static_folder='static')

@bp.route("/", methods=("GET","POST"))
def index():
    if request.method == "GET":
        try:
            session['game_started']
        except KeyError:
            return redirect(url_for("welcome.index"))
        else:
            if not session['game_started']:
                error = "Game not started. Please go to Game Setup to begin."
                flash(error)     
    # RESET between sessions??????  
    db = get_db()
    error = None

    if request.method == "POST":
        if 'next_player' in request.form:
            update_net_worth_turn(db)
            current_player_order, session['current_turn'] = next_player(db, session['player_dict'][str(session['current_player_id'])][1], session['no_of_players'], session['current_turn'])
            session['current_player_id'] = list({id for id in session['player_dict'] if session['player_dict'][id][1] == current_player_order})[0]

            return render_template("gameplay/index.html", players=session['player_dict'], current_turn=session['current_turn'], current_player_id=session['current_player_id'], net_worths=session['net_worths'], property_names=session['property_names'])

        elif 'pass_go' in request.form:
            go(db)
            
        elif 'land_on_go' in request.form:
            go(db,True)

        elif 'purchase_property' in request.form:
            property_name = request.form['property_name']
            purchase_property(db, session['current_player_id'], property_name, session['current_turn'])
        
        elif 'rent' in request.form:
            property_name = request.form['property_name']
            rent_due, comment = rent(db, session['current_player_id'], property_name, session['current_turn'])
            flash(comment)

        else:
            pass

        net_worth_table, session['net_worths'] = get_net_worth(db)

    return render_template("gameplay/index.html", players=session['player_dict'], current_turn=session['current_turn'], current_player_id=session['current_player_id'], net_worths=session['net_worths'], property_names=session['property_names'])

