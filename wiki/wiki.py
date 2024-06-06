from flask import Flask, jsonify, request
import requests, os, urllib.parse, json
from dotenv import load_dotenv
import mysql.connector

load_dotenv('./.env')
'''
Environment Variables Needed
DB_PSWD:        password for db user mentioned in connection
'''
debug = lambda p : print('+'*50, p, '+'*50, sep='\n')

app = Flask(__name__)
cache_period = 1
todoist = 'https://44.213.185.12:8000'

sql = mysql.connector.connect(
    host="mysqld",
    port=3306,
    user="cse617",
    password=os.environ.get("DB_PSWD"),
    database="final"
)
dbcursor = sql.cursor()

### SQL QUERIES ###
insert_query = lambda p : f"INSERT INTO wiki (city, description) VALUES ('{p['city']}', {json.dumps(p['description'])});"
city_count = lambda c : f"SELECT COUNT(*) FROM wiki WHERE city='{c}'"
recent_record = lambda c : f"SELECT *,TIMESTAMPDIFF(MINUTE, timestamp, NOW()) AS t_diff FROM wiki WHERE city='{c}' ORDER BY timestamp DESC LIMIT 1;"


wiki_object = lambda cols, vals : {cols[i]: vals[i] for i in range(len(cols))} 

@app.route('/')
def index():
    return '<h1>Wikipedia Server</h1>'

@app.route('/insert', methods=['POST'])
def db_insert():
    payload = request.json
    debug(f'inserted new record for: {payload["city"]}')
    try:
        dbcursor.execute(insert_query(payload))
#        dbcursor.execute(insert, (payload['city'], payload['description']))
        sql.commit()
        return {"msg" : "insert success"}
    except Exception as e:
        return {"some error occured": str(e)}

def table_cols(table):
    dbcursor.execute(f"DESCRIBE {table}")
    rows = dbcursor.fetchall()
    cols = [cell[0] for cell in rows]
    return cols

# @headers: Authorization of the todoist app
# @paramas: project_name of the todoist app

@app.route('/wiki')
def wiki():
    headers = { 'Authorization': request.headers.get('Authorization') }
    params = { 'project_name': request.args.get('project_name') }
    cities = requests.get(todoist+f'/todoist', headers=headers, params=params, verify=False).json()
    
    wikis = []
    base = "https://en.wikipedia.org/w/api.php"
    param = lambda city : {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True, 
        "explaintext": True,
        "redirects": 1,
        "titles": city.split(',')[0]
    }

    def insert_callback(city):
        data = requests.get(base, params=param(city)).json()
        page_id = list(data["query"]["pages"].keys())[0]
        description = data["query"]["pages"][page_id]["extract"]
        payload = {"city": city, "description": description}
        requests.post('https://localhost:7000/insert', json=payload, verify=False)

    try:
        for city in cities:
            city = city if city.split(',')[-1].endswith('US') else city + ',US'
            dbcursor.execute(city_count(city))
            records = dbcursor.fetchone()[0]
            if records != 0:
                dbcursor.execute(recent_record(city))
                record_data = dbcursor.fetchone()
                if record_data[-1] > cache_period:
                    resp = insert_callback(city)
            else:
                insert_callback(city)

            dbcursor.execute(recent_record(city))
            record_data = dbcursor.fetchone()
            wikis.append(wiki_object(table_cols('wiki'), record_data))

        return jsonify(wikis)

    except Exception as e:
        return {"wiki endpoint error occured": str(e)}
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', ssl_context="adhoc", port=7000)
