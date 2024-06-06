from flask import Flask, jsonify, request
import requests, os, urllib.parse
from dotenv import load_dotenv
import mysql.connector

'''
Environment Variables Needed
WEATHER_TOKEN:  token for weather api 
DB_PSWD:        password for db user mentioned in connection
'''

load_dotenv('./.env')
debug = lambda p : print('+'*50, p, '+'*50, sep='\n')

app = Flask(__name__)
cache_period = 1
todoist = 'https://44.213.185.12:8000'

sql = mysql.connector.connect(
    host="172.17.136.179",
    port=3307,
    user="cse617",
    password=os.environ.get("DB_PSWD"),
    database="final"
)
dbcursor = sql.cursor()

### SQL QUERIES ###
insert_query = lambda p : f"INSERT INTO weather (city, feels_like, humidity, pressure, temp, temp_max, temp_min) VALUES ('{p['city']}', {p['feels_like']}, {p['humidity']}, {p['pressure']},  {p['temp']}, {p['temp_max']}, {p['temp_min']});"

city_count = lambda c : f"SELECT COUNT(*) FROM weather WHERE city='{c}'"
recent_record = lambda c : f"SELECT *,TIMESTAMPDIFF(MINUTE, timestamp, NOW()) AS t_diff FROM weather WHERE city='{c}' ORDER BY timestamp DESC LIMIT 1;"



def table_cols(table):
    dbcursor.execute(f"DESCRIBE {table}")
    rows = dbcursor.fetchall()
    cols = [cell[0] for cell in rows]
    return cols


weather_object = lambda cols, vals : {cols[i]: vals[i] for i in range(len(cols))} 

@app.route('/')
def index():
    return '<h1>Weather Flask Server</h1>'


@app.route('/insert', methods=['POST'])
def db_insert():
    payload = request.json
    debug(f'inserted new record for: {payload["city"]}')
    try:
        dbcursor.execute(insert_query(payload))
        sql.commit()
        return {"msg" : "insert success"}
    except Exception as e:
        return {"some error occured": str(e)}

@app.route('/geocode/<location>')
def geocoding(location):
    geocode = f'http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={os.environ.get("WEATHER_TOKEN")}'
    try:
        resp = requests.get(geocode).json()
        return jsonify({"lat": resp[0]['lat'], "lon": resp[0]['lon']})

    except Exception as e:
        return jsonify({"some error occured", str(e)})


# @header:  requires todoist authorization token
# @params:  project_name of the todoist project

@app.route('/weather')
def weather():
    weathers = []
    headers = { "Authorization": request.headers.get('Authorization') }
    params = { 'project_name': request.args.get('project_name') }
    weather_token = os.environ.get('WEATHER_TOKEN')
    base = lambda city : f'https://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(city)}&appid={weather_token}'

    def insert_callback(ex):
        resp = requests.get(base(ex))
        if resp.ok:
            resp = resp.json()
            resp["main"]["city"] = ex
            requests.post('https://localhost:5000/insert', json=resp["main"], verify=False)

    try:
        cities = requests.get(todoist+f'/todoist', headers=headers, params=params, verify=False).json()

        for city in cities:
            city = city if city.split(',')[-1].endswith('US') else city + ',US'
            dbcursor.execute(city_count(city))
            records = dbcursor.fetchone()[0]
            if records != 0:
                dbcursor.execute(recent_record(city))
                record_data = dbcursor.fetchone()
                if record_data[-1] > cache_period:
                    insert_callback(city)

            else:
                insert_callback(city)

            dbcursor.execute(recent_record(city))
            record_data = dbcursor.fetchone()
            if record_data != None:
                weathers.append(weather_object(table_cols('weather'), record_data))

        return jsonify(weathers)
    except Exception as e:
        return {"weather endpoint error occured": str(e)}

if __name__ == "__main__":
    app.run(host='0.0.0.0', ssl_context="adhoc", port=5000)
