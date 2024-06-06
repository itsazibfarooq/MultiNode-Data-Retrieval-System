from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Todoist Server</h1>'

base = 'https://api.todoist.com/rest/v2'
debug = lambda x : print('+'*50, x, '+'*50, sep='\n')

@app.route('/todoist')
def todoist():
    headers = {"Authorization": request.headers.get('Authorization')}
    project_name = request.args.get('project_name')
    
    id = project_id(project_name, headers)
    params = { 'project_id': id }

    resp = requests.get(f'{base}/tasks', headers=headers, params=params)

    tasks = resp.json()
    cities = [tasks[i]['content'].split(' - ')[0] for i in range(len(tasks))] 
    return cities


def project_id(project_name, headers):
    response = requests.get(
        f'{base}/projects',
        headers=headers
    )
    projects = response.json()
    project = next((p for p in projects if p['name'] == project_name), None)
    return project['id']

if __name__ == "__main__":
    app.run(host="0.0.0.0", ssl_context='adhoc', port=8000)
