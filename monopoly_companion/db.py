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

def init_data():
    db = get_db()

    df_tables = ['action_type','game_version','players','property']
    for df in df_tables:
        data = pd.read_json(current_app.open_resource('static/' + df + '.json'))
        data.to_sql(df, con=db, if_exists="replace", index=False)

def init_property_ownership(game_version_id):
    db = get_db()

    properties = db.execute(
        "SELECT * FROM property WHERE game_version_id = ?",
        (game_version_id,)
        ).fetchall()
    
    ownership_not_empty = db.execute(
        "SELECT EXISTS (SELECT 1 FROM property_ownership)"
        ).fetchall()
    print(ownership_not_empty[0][0])
    if ownership_not_empty[0][0] == 1:
        db.execute(
            "DELETE FROM property_ownership"
        )
        db.commit()

    for prop in properties:
        db.execute(
            "INSERT INTO property_ownership VALUES (?, 1, FALSE, 0, 0, 0)",
            (prop['property_id'],)
        )
    db.commit()
    return 

def update_number_owned():
    # join property and property_ownership tables on property_id
    # count how many properties owned within city by owner
    # insert the count into property_ownership.number_owned
    return 

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    