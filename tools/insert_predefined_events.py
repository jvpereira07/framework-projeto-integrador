"""
Script to insert predefined events with condition_type 'proximidade'.
Each event has condition_data with posx, posy, raio.
"""
import sqlite3
import json

DB = 'assets/data/data.db'

def insert_event(name, condition_type, condition_data, actionType, action_json, cooldown, isloop, action_data='{}'):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO Events (name, condition_code, actionType, action_json, cooldown, isloop, condition_type, condition_data, action_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, '', actionType, action_json, cooldown, int(isloop), condition_type, condition_data, action_data))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Example: spawn mob near (1600, 468) within 100px
    insert_event(
        name='spawn_mob_sala1_1600_468',
        condition_type='proximidade',
        condition_data=json.dumps({"posx": 1600, "posy": 468, "raio": 100}),
        actionType='spawn',
        action_json=json.dumps({"num_mob": 2, "id_mob": 5, "x": 1600, "y": 468}),
        cooldown=3.0,
        isloop=False
    )
    print("Inserted example event")
