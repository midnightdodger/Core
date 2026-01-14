import json
import sqlite3
import secrets

def write_json(json_file, data):
    with open(json_file,'w') as file:
        json.dump(data, file)

def get_json(json_file):
    with open(json_file,"r") as file:
        return json.load(file)

def json_data(data, key):
    if key in data:
        return data[key]
    else:
        return None

def get_key(local):
    with open(local,"r") as key:
        data = key.read()
    if data != "":
        return data
    else:
        with open(local,"w") as key:
            key.write(secrets.token_hex(32))
        with open(local,"r") as key:
            data = key.read()
        return data

