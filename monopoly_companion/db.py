import sqlite3
import click
from flask import current_app, g, session
import pandas as pd

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    
def init_data(db):
    db.executescript(
        """
        DELETE FROM action_type;
        DELETE FROM game_version;
        DELETE FROM players;
        DELETE FROM property;
        DELETE FROM special_counter;
        DELETE FROM net_worth;
        DELETE FROM net_worth_log;
        DELETE FROM transactions;
        DELETE FROM property_ownership;
        VACUUM;
        """
    )
    df_tables = ['action_type', 'game_version', 'players', 'property']
    for df in df_tables:
        data = pd.read_csv(current_app.open_resource('static/' + df + '.csv'))
        data.to_sql(df, con=db, if_exists="append", index=False)

    db.commit()
    session.clear()
    return

def init_property_ownership(db, game_version_id):
    properties = db.execute(
        "SELECT * FROM property WHERE game_version_id = ?",
        (game_version_id,)
        ).fetchall()
    
    # commented out because syntax could be useful in another case but we already delete property_ownership data in init_data
    # ownership_not_empty = db.execute(
    #     "SELECT EXISTS (SELECT 1 FROM property_ownership)"
    #     ).fetchall()
    # print(ownership_not_empty[0][0])
    # if ownership_not_empty[0][0] == 1:
    #     db.execute(
    #         "DELETE FROM property_ownership"
    #     )

    for prop in properties:
        db.execute(
            "INSERT INTO property_ownership VALUES (?, 1, FALSE, 0, 0, 0, FALSE)",
            (prop['property_id'],)
        )
    db.commit()

    update_number_owned(db)
    update_max_number_owned(db)

    return 

def update_max_number_owned(db):
    # update the "max_number_owned" field in the property_ownership table to enable comparison to number owned to determine "monopoly" column
    # only needs to be called once at the beginning
    cities = db.execute(
        """
        SELECT DISTINCT city from property 
        """
    ).fetchall()
    
    for row in cities:
        db.execute(
            """
            UPDATE property_ownership
            SET max_number_owned = 
                (SELECT 
                COUNT(property.property_id) AS max_number_owned_in_city
                from 
                property
                WHERE
                property.city = ?)
            WHERE property_id IN 
                (SELECT
                property_id
                FROM
                property
                WHERE
                property.city = ?)
            """,
            (row['city'], row['city'])
        )

    db.commit()
    return

def update_number_owned(db):
    # get a joined table containing owner id-city combos with counts
    city_ownership = db.execute(
        """
        SELECT 
        property_ownership.owner_player_id,
        property.city,
        COUNT(property.property_id) AS number_owned_in_city
        from 
        property_ownership 
        LEFT JOIN 
        property
        ON
        property_ownership.property_id = property.property_id
        GROUP BY
        property.city,
        property_ownership.owner_player_id;
        """
    )

    # for each row in the owner-city combo table, 
    # collect the variables we need for update and update the ownership table. 
    # This requires us to check which properties are in the cities, since ownership table doesn't have a city field. 
    for city_owner_combo in city_ownership:
        number_owned = city_owner_combo['number_owned_in_city']
        owner_id = city_owner_combo['owner_player_id']
        city = city_owner_combo['city']
        
        db.execute(
            """
            UPDATE 
            property_ownership
            SET 
            number_owned = ?
            WHERE
            owner_player_id = ? 
            AND 
            property_id IN 
                (SELECT
                property_id
                FROM
                property
                WHERE
                property.city = ?)
            """,
            (number_owned, owner_id, city,)
        )
        
    db.commit()

    return 

def starting_cash(no_of_players, player_names, total_cash, starting_cash_per_player):
    # at the beginning of the game, calculate the starting cash values of the bank, based on number of players and starting cash per player  
    # create a dictionary with keys = player_ids and value a list with name and starting cash
    player_names_incl_static = ["Bank", "Free Parking"] + player_names    
    player_starting_cash = {}
    
    bank_starting_cash = total_cash - (starting_cash_per_player * no_of_players)

    for player in player_names_incl_static:
        player_id = player_names_incl_static.index(player)+1
        if player == "Bank":
            player_starting_cash[1] = ["Bank", bank_starting_cash]
        elif player == "Free Parking":
            player_starting_cash[2] = ["Free Parking", 0]
        else:
            player_starting_cash[player_names_incl_static.index(player)+1] = [player, starting_cash_per_player] 

    return player_starting_cash

def get_gross_property_value(db):
    # get all rows with player_id and sum of property price (value) owned by that player

    gross_property_value = db.execute(
        """
        SELECT
        players.player_id,
        IFNULL(SUM(property.price), 0) AS gross_property_value
        from 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.player_id = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.property_id
        GROUP BY
        property_ownership.owner_player_id
        ORDER BY 
        players.player_id ASC 
        """
    ).fetchall()

    return gross_property_value

def get_mortgaged_property_value(db):
    # get all rows with player_id and sum of mortgage_value field for all owned property that is currently mortgaged 
    mortgaged_property_value = db.execute(
        """
        SELECT
        players.player_id,
        IFNULL(SUM(property.mortgage_value), 0) AS mortgaged_property_value
        FROM 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.player_id = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.property_id
        WHERE 
        property_ownership.mortgaged = TRUE        
        GROUP BY
        property_ownership.owner_player_id
        ORDER BY 
        players.player_id ASC 
        """
    ).fetchall()

    return mortgaged_property_value

def get_unmortgaged_property_value(db):
    # get all rows with player_id and sum of price field for all owned property that is not currently mortgaged 
    unmortgaged_property_value = db.execute(
        """
        SELECT
        players.player_id,
        IFNULL(SUM(property.price), 0) AS unmortgaged_property_value
        FROM 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.player_id = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.property_id
        WHERE 
        property_ownership.mortgaged = FALSE        
        GROUP BY
        property_ownership.owner_player_id
        ORDER BY 
        players.player_id ASC 
        """
    ).fetchall()

    return unmortgaged_property_value

def get_property_value(db, player_names):
    # create a dictionary with key = player_id and values being a list of player name and 
    # sum of the results of the mortgaged_property_value and unmortgaged_property_value functions 

    property_value = {}
    
    player_names_incl_static = ["Bank", "Free Parking"] + player_names
    mortgaged_property_value = get_mortgaged_property_value(db)
    unmortgaged_property_value = get_unmortgaged_property_value(db)
    gross_property_value = get_gross_property_value(db)
    improvement_value = get_improvement_value(db)
        
    for player in player_names_incl_static:
        property_value[player_names_incl_static.index(player)+1] = [0, 0, 0, 0, 0, 0]
        property_value[player_names_incl_static.index(player)+1][0] = player

    for row in mortgaged_property_value:
        property_value[row['player_id']][1] = row['mortgaged_property_value']

    for row in unmortgaged_property_value:
        property_value[row['player_id']][2] = row['unmortgaged_property_value']
    
    for key in property_value.keys():
        property_value[key][3] = property_value[key][1] + property_value[key][2]

    for row in gross_property_value:
        property_value[row['player_id']][4] = row['gross_property_value']

    for row in improvement_value:
        property_value[row['player_id']][5] = row['improvement_value']

    return property_value

def get_improvement_value(db):
    # get all rows with player_id and the sum of the value of all houses and hotels on property owned by that player
    improvement_values = db.execute(
        """
        SELECT
        players.player_id,
        IFNULL(CASE WHEN property_ownership.hotels = 1 THEN SUM(5* property.house_cost) ELSE SUM(property_ownership.houses * property.house_cost) END, 0) AS improvement_value
        FROM 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.player_id = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.property_id
        GROUP BY
        players.player_id
        ORDER BY 
        players.player_id ASC 
        """
    ).fetchall()

    return improvement_values

def get_net_worth(db):
    # get net_worth rows for all players to represent current net_worth
    current_net_worth_table = db.execute(
        """
        SELECT 
        net_worth_id,
        net_worth_time,
        player_id,
        cash_balance,
        net_property_value,
        improvement_value,
        gross_property_value,
        net_worth
        FROM
        net_worth
        """
    ).fetchall()
    

    try:
        for row in current_net_worth_table:
            session['net_worths'][str(row['player_id'])][0] = row['cash_balance']
            session['net_worths'][str(row['player_id'])][1] = row['net_property_value']
            session['net_worths'][str(row['player_id'])][2] = row['improvement_value']
            session['net_worths'][str(row['player_id'])][3] = row['gross_property_value']
            session['net_worths'][str(row['player_id'])][4] = row['net_worth']
    except:
        session['net_worths'] = {}
        for row in current_net_worth_table:
            session['net_worths'][str(row['player_id'])] = [0, 0, 0, 0, 0]
            session['net_worths'][str(row['player_id'])][0] = row['cash_balance']
            session['net_worths'][str(row['player_id'])][1] = row['net_property_value']
            session['net_worths'][str(row['player_id'])][2] = row['improvement_value']
            session['net_worths'][str(row['player_id'])][3] = row['gross_property_value']
            session['net_worths'][str(row['player_id'])][4] = row['net_worth']
        
    return current_net_worth_table, session['net_worths']

def update_net_worth_turn(db):
    db.execute("UPDATE net_worth SET turn = ? WHERE player_id IN (1, 2, ?)",
               (session['current_turn'], session['current_player_id'])
               )
    return

def next_player(db, current_player_order, no_of_players, turn):
    # increment the current_player_order up to the no_of_players, at which point it restarts at order 1 and increments turn

    if current_player_order == no_of_players:
        current_player_order = 1 
        turn += 1
        log_net_worth(db) # think about how to unlog net_worth when previous_player or undo_action
    else:
        current_player_order += 1
    
    db.commit()
    return current_player_order, turn

def previous_player(current_player_order, no_of_players, turn):
    # decrement the current_player_order down to 1, at which point it restarts at no_of_players and decrements turn

    if current_player_order == 1:
        current_player_order = no_of_players
        turn -= 1
    else:
        current_player_order -= 1
    return current_player_order, turn

def undo_action():
    return

# this section contains the functions for action-type database updates. This will make the code in index() easier to understand.
def log_net_worth(db):
    # add rows to net_worth_log table that contain the most recent net_worth data. This is to be used whenever a turn ends.
    
    # copy all data from net_worth to log_net_worth 
    db.execute(
        """
        INSERT INTO net_worth_log (net_worth_time, turn, player_id, cash_balance, net_property_value, improvement_value, gross_property_value, net_worth)
        SELECT net_worth_time, turn, player_id, cash_balance, net_property_value, improvement_value, gross_property_value, net_worth FROM net_worth
        """
    )
    return

def record_transaction(db, turn, party_player_id, counterparty_player_id, action_type_id, property_id=None, cash_received=None, cash_paid=None, asset_value_received=None, asset_value_paid=None):
    db.execute(
        """
        INSERT INTO transactions (turn, party_player_id, counterparty_player_id, action_type_id, property_id, cash_received, cash_paid, asset_value_received, asset_value_paid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (turn, party_player_id, counterparty_player_id, action_type_id, property_id, cash_received, cash_paid, asset_value_received, asset_value_paid)
    )
    return

def purchase_property(db, current_player_id, property_name, turn):
    # buy property from the bank

    # get the price
    property_id, price = db.execute(
        "SELECT property_id, price FROM property WHERE property_name = ?",
        (property_name,)
    ).fetchone()

    # update net_worth with subtracted price from player cash and added price to net and gross property values 
    db.execute(
        """
        UPDATE net_worth
        SET cash_balance = cash_balance - ?,
            net_property_value = net_property_value + ?,
            gross_property_value = gross_property_value + ?
        WHERE player_id = ?;

        UPDATE net_worth
        SET cash_balance = cash_balance + ?,
            net_property_value = net_property_value - ?,
            gross_property_value = gross_property_value - ?
        WHERE player_id = ?
        """,
        (price, price, price, current_player_id, price, price, price, 1)
    )
    
    # assign ownership to player    
    db.execute(
        """
        UPDATE property_ownership
        SET owner_player_id = ?
        WHERE property_id = ?
        """,
        (current_player_id, property_id)
    )
    update_number_owned(db)
    
    # add the transaction to transactions table
    record_transaction(db, turn, current_player_id, 1, 1, property_id, None, price, price, None)
    db.commit()
    return

def trade_property():
    # trade property (has more requirements, leave till end)
    return

def rent(db, current_player_id, property_name, turn):
    # pay rent to owner on property

    # get rent due (consider mortgaged, monopoly, houses, and hotels)
    property_details = db.execute(
        "SELECT * FROM property LEFT JOIN property_ownership on property.property_id = property_ownership.property_id WHERE property.property_name = ?",
        (property_name,)
    ).fetchall()

    if property_details['owner_player_id'] == 1:
        rent_due = 0
        comment = "Property owned by bank! No rent due."

    elif property_details['mortgaged'] == True:
        rent_due = 0
        comment = "Property mortgaged! No rent due."
    
    elif property_details['hotels'] == 1:
        rent_due = property_details['rent_hotel']
        comment = "Property with Hotel: " + str(rent_due) + " due."

    elif property_details['houses'] > 0:
        if property_details['houses'] == 1:
            rent_due = property_details['rent_one_house']
            comment = "Property with one house: " + str(rent_due) + " due."
        if property_details['houses'] == 2:
            rent_due = property_details['rent_two_houses']
            comment = "Property with two houses: " + str(rent_due) + " due."            
        if property_details['houses'] == 3:
            rent_due = property_details['rent_three_houses']
            comment = "Property with three houses: " + str(rent_due) + " due."  
        if property_details['houses'] == 4:
            rent_due = property_details['rent_four_houses']
            comment = "Property with four houses: " + str(rent_due) + " due."    

    elif property_details['monopoly'] and property_details['property_type'] == "Street":
        rent_due = property_details['rent_monopoly']
        comment = "Property in a Monopoly: " + str(rent_due) + " due."
    
    elif property_details['property_type'] == "Station" and property_details['number_owned'] > 1:
        if property_details['number_owned'] == 2:
            rent_due = property_details['rent_two_owned']
            comment = "Two stations owned: " + str(rent_due) + " due."
        elif property_details['number_owned'] == 3:
            rent_due = property_details['rent_three_owned']
            comment = "Three stations owned: " + str(rent_due) + " due."
        elif property_details['number_owned'] == 4:
            rent_due = property_details['rent_four_owned']
            comment = "Four stations owned: " + str(rent_due) + " due."
        
    elif property_details['property_type'] == "Utility":
        if property_details['number_owned'] == 1:
            rent_due = property_details['rent_multiplier_one_owned']
            comment = "One utility owned. Multiply the dice roll by: " + str(rent_due) + "."
        else:
            rent_due = property_details['rent_multiplier_two_owned']
            comment = "Two utilities owned. Multiply the dice roll by: " + str(rent_due) + "."
    
    else:
        rent_due = property_details['rent_basic']
        comment = "Rent due: " + str(rent_due) + "."

    # update net_worth with cash exchange
    db.execute(
        """
        UPDATE net_worth
        SET cash_balance = CASE
            WHEN player_id = ? THEN cash_balance + ?
            WHEN player_id = ? THEN cash_balance - ?
            END
        WHERE player_id IN (?,?)
        """,
        (property_details['owner_player_id'], rent_due, current_player_id, rent_due, property_details['owner_player_id'], current_player_id)
    )
    
    # add the transaction to transactions table
    record_transaction(db, turn, current_player_id, property_details['owner_player_id'], 2, property_details['property_id'], cash_paid=rent_due)
    db.commit()

    return

def go(db, landed_on=False):
    # pass or land on go
   
    # if player lands on and double_go rule in effect, increase player's cash balance by 2*game_version.go_value and increment special counter
    if landed_on and session['double_go']:
        double_go_value = session['go_value']*2
        db.execute(
            """
            UPDATE net_worth
            SET cash_balance = 
                CASE 
                    WHEN player_id = ? THEN cash_balance + ?
                    WHEN player_id = 1 THEN cash_balance - ?
                END
            WHERE player_id IN (1, ?)
            """,
            (session['current_player_id'], double_go_value, double_go_value, session['current_player_id'])
            )
        # increment special counter TBD 
        
        # record transaction 
        record_transaction(db, session['current_turn'], session['current_player_id'], 1, 4, cash_received=double_go_value)

    # if player passes (or lands and double_go rule not in effect), only increase player's cash balance by game_version.go_value
    else:
        db.execute(
            """
            UPDATE net_worth
            SET cash_balance = 
                CASE 
                    WHEN player_id = ? THEN cash_balance + ?
                    WHEN player_id = 1 THEN cash_balance - ?
                END
            WHERE player_id IN (1, ?)
            """,
            (session['current_player_id'], session['go_value'], session['go_value'], session['current_player_id'])
            )
    
        # record transaction
        record_transaction(db, session['current_turn'], session['current_player_id'], 1, 3, cash_received=session['go_value'])

    db.commit()
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
