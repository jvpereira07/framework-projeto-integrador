"""
Small helper to register two events directly into assets/data/data.db:
- spawn_mob_near_1174_192: spawns 3 mobs (id 2) when player is within 150px of (1174,192)
- spawn_breakable_near_300_100: spawns 1 breakable (id 4) when player is within 100px of (300,100)

This script inserts rows into the Events table with condition_code strings that will be eval()-ed by EventControl.load().
Be careful: eval is dangerous. Only run this in a trusted environment.
"""
import sqlite3
import json

DB = 'assets/data/data.db'

def insert_event(name, condition_code, actionType, action_dict, cooldown, isloop):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Ensure table exists
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Events (
            id INTEGER PRIMARY KEY,
            name TEXT,
            condition_code TEXT,
            actionType TEXT,
            action_json TEXT,
            cooldown REAL,
            isloop INTEGER
        )
    ''')
    # Insert
    cur.execute('INSERT INTO Events (name, condition_code, actionType, action_json, cooldown, isloop) VALUES (?, ?, ?, ?, ?, ?)',
                (name, condition_code, actionType, json.dumps(action_dict), cooldown, int(bool(isloop))))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Event A: spawn mob near (1174,192) within 150px
    name_a = 'spawn_mob_near_1174_192'
    # The condition_code must eval to a callable: lambda: bool
    # Use __import__('core.entity').PControl.get_main_player() to obtain the player object at runtime
    # Condition: True if any player in PControl.Players is within 150px of (1174,192)
    cond_a = (
        "lambda: any((( (p.posx - 1174)**2 + (p.posy - 192)**2 )**0.5) <= 150 for p in __import__('core.entity').PControl.Players)"
    )
    action_a = {"num_mob": 3, "id_mob": 2, "x": 1174, "y": 192}
    insert_event(name_a, cond_a, 'spawn', action_a, 10.0, True)

    # Event B: spawn breakable near (300,100) within 100px
    name_b = 'spawn_breakable_near_300_100'
    # Condition: True if any player in PControl.Players is within 100px of (300,100)
    cond_b = (
        "lambda: any((( (p.posx - 300)**2 + (p.posy - 100)**2 )**0.5) <= 100 for p in __import__('core.entity').PControl.Players)"
    )
    action_b = {"num_breakable": 1, "id_breakable": 4, "x": 300, "y": 100}
    insert_event(name_b, cond_b, 'spawn_breakable', action_b, 30.0, False)

    print('Inserted two events into', DB)
