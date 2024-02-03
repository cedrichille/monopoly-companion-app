import sqlite3
import click
from flask import current_app, g
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
    df_tables = ['action_type','game_version','players','property']
    for df in df_tables:
        data = pd.read_json(current_app.open_resource('static/' + df + '.json'))
        data.to_sql(df, con=db, if_exists="replace", index=False)
    
    db.executescript(
        """
        DELETE FROM special_counter;
        DELETE FROM net_worth;
        DELETE FROM transactions;
        DELETE FROM property_ownership;
        VACUUM;
        """
    )
 
    db.commit()
    return

def init_property_ownership(db, game_version_id):
    properties = db.execute(
        "SELECT rowid, * FROM property WHERE game_version_id = ?",
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
            "INSERT INTO property_ownership VALUES (?, 1, FALSE, 0, 0, 0)",
            (prop['rowid'],)
        )
    db.commit()

    update_number_owned(db)

    return 

def update_number_owned(db):
    # get a joined table containing owner id-city combos with counts
    city_ownership = db.execute(
        """
        SELECT 
        property_ownership.owner_player_id,
        property.city,
        COUNT(property.rowid) AS number_owned_in_city
        from 
        property_ownership 
        LEFT JOIN 
        property
        ON
        property_ownership.property_id = property.rowid
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
            rowid IN 
                (SELECT
                rowid
                FROM
                property
                WHERE
                property.city = ?)
            """,
            (number_owned, owner_id, city,)
        )
        
    db.commit()

    return 

def starting_cash(db, no_of_players, player_names, total_cash, starting_cash_per_player):
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
        players.rowid,
        IFNULL(SUM(property.price), 0) AS gross_property_value
        from 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.rowid = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.rowid
        GROUP BY
        property_ownership.owner_player_id
        ORDER BY 
        players.rowid ASC 
        """
    ).fetchall()

    return gross_property_value

def get_mortgaged_property_value(db):
    # get all rows with player_id and sum of mortgage_value field for all owned property that is currently mortgaged 
    mortgaged_property_value = db.execute(
        """
        SELECT
        players.rowid,
        IFNULL(SUM(property.mortgage_value), 0) AS mortgaged_property_value
        FROM 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.rowid = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.rowid
        WHERE 
        property_ownership.mortgaged = TRUE        
        GROUP BY
        property_ownership.owner_player_id
        ORDER BY 
        players.rowid ASC 
        """
    ).fetchall()

    return mortgaged_property_value

def get_unmortgaged_property_value(db):
    # get all rows with player_id and sum of price field for all owned property that is not currently mortgaged 
    unmortgaged_property_value = db.execute(
        """
        SELECT
        players.rowid,
        IFNULL(SUM(property.price), 0) AS unmortgaged_property_value
        FROM 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.rowid = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.rowid
        WHERE 
        property_ownership.mortgaged = FALSE        
        GROUP BY
        property_ownership.owner_player_id
        ORDER BY 
        players.rowid ASC 
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
        property_value[row['rowid']][1] = row['mortgaged_property_value']

    for row in unmortgaged_property_value:
        property_value[row['rowid']][2] = row['unmortgaged_property_value']
    
    for key in property_value.keys():
        property_value[key][3] = property_value[key][1] + property_value[key][2]

    for row in gross_property_value:
        property_value[row['rowid']][4] = row['gross_property_value']

    for row in improvement_value:
        property_value[row['rowid']][5] = row['improvement_value']

    return property_value

def get_improvement_value(db):
    # get all rows with player_id and the sum of the value of all houses and hotels on property owned by that player
    improvement_values = db.execute(
        """
        SELECT
        players.rowid,
        IFNULL(CASE WHEN property_ownership.hotels = 1 THEN SUM(5* property.house_cost) ELSE SUM(property_ownership.houses * property.house_cost) END, 0) AS improvement_value
        FROM 
        players
        LEFT JOIN 
        property_ownership
        ON
        players.rowid = property_ownership.owner_player_id
        LEFT JOIN
        property
        ON
        property_ownership.property_id = property.rowid
        GROUP BY
        players.rowid
        ORDER BY 
        players.rowid ASC 
        """
    ).fetchall()

    return improvement_values

def get_net_worth(db):
    # get most recent net_worth row for all players to represent current net_worth

    current_net_worths = {}

    current_net_worth_table = db.execute(
        """
        SELECT 
        max(net_worth_time),
        player_id,
        cash_balance,
        net_property_value,
        improvement_value,
        gross_property_value,
        net_worth
        FROM
        net_worth
        GROUP BY
        player_id
        ORDER BY 
        player_id
        """
    ).fetchall()

    for row in current_net_worth_table:
        current_net_worths[row['player_id']] = [0, 0, 0, 0, 0]
        current_net_worths[row['player_id']][0] = row['cash_balance']
        current_net_worths[row['player_id']][1] = row['net_property_value']
        current_net_worths[row['player_id']][2] = row['improvement_value']
        current_net_worths[row['player_id']][3] = row['gross_property_value']
        current_net_worths[row['player_id']][4] = row['net_worth']
        
    return current_net_worth_table, current_net_worths

def update_net_worth(db):
    return

def next_player(current_player_order, no_of_players, turn):
    # increment the current_player_order up to the no_of_players, at which point it restarts at order 1 and increments turn

    if current_player_order == no_of_players:
        current_player_order = 1 
        turn += 1
    else:
        current_player_order += 1
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
