# Monopoly Companion App
This project aims to build a companion app to the popular board game "Monopoly". 

## Purpose 
The app's aim is to help players track, visualize, and analyze real games played. The app is intended to be used alongside the board game, capturing all moves made and their outcomes. 

The purpose is to enrich Monopoly players' understanding of the game. The app tracks and shows statistics and trends on player wealth in real time, as well as information on the value of properties. It effectively provides a real-time scoreboard and can help players factually reflect on strategic choices, as well as the role of luck in determining the outcome of the game. 

## Features
Features include:
- Selection of popular versions of Monopoly to determine property names and values
- Ability to add custom versions of Monopoly, including property names and values
- Selection of number of players and their respective game pieces
- Turn count display
- Current player display
- Selection of roll outcome (e.g., landing on chance/community chest, a property, or being sent to jail) and implications (e.g., money paid and received, property ownership changes, or going to jail)
- Real-time tracking of all players' cash balances and property ownership 
- Storage of turn-by-turn events and player wealth
- Visual display of key player statistics over time (e.g., player cash wealth, player property wealth, times sent to jail, net income from chance/community chest, income generated from properties, etc.)
- Visual display of key property statistics over time (e.g., income generated from property, times landed on property, etc.)
- Ability to save and export game statistics

## Structure and Technical Info
The Monopoly Companion App is a web application built on the Flask framework. 
Thoughts:
- SQL database or pandas? SQLAlchemy, PostgreSQL, SQLite, MySQL...?
    - Dev in SQLite and then transition to Postgres for deploy (if we get that far). Good to get experience with setting up the database and CRUD operations.
    - But won't be using SQL syntax, SQLAlchemy will be needed in any case. Good to have this additional skill, but maybe in parallel practice SQL itself?
- How does app structure differ from web interface? 
    - Need to map out:
        - Database schema 
        - Possible operations on database for game moves (CRUD + export)
        - html templates
        - Forms in html or WTForms
        - Flask routes 
        - Flask requests
        
- Integrate Dash for graph representations? 

Dependencies:
- Flask
- Flask-SQLAlchemy
- sqlite3 (included in python)
- WTForms
- Bootstrap-Flask

## Parking Lot
- PRIORITY 
- unlog last net_worth_log addition
- undo last transaction   
- Names have to be unique
- Player order has to be unique
- Max number of players
- Once registration is done, have to start over to make changes, or create a dedicated edit screen. 
- Storing turn information between stats views etc. Maybe not an issue if we only have stats templates without an additional route
- Clear tables when session ends 
