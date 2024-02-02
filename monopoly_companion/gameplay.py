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

    return render_template ("gameplay/index.html")

def next_turn():
    return

def previous_turn():
    return

def undo_action():
    return

# this section contains the functions for action-type database updates. This will make the code in index() easier to understand.
def purchase_property():
    # buy property 

    return

def trade_property():
    # trade property (has more requirements, leave till end)
    return

def rent():
    # pay rent to owner on property
    return

def go():
    # pass or land on go
    return

def build():
    # build a house or hotel
    return

def mortgage():
    # mortgage or unmortgage a property
    return

def special_field():
    # chance, community chest, or free parking
    return

def tax():
    # income or luxury tax
    return

def jail():
    # enter jail and leave jail
    return
