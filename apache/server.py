import os
import secrets
from urllib.parse import urlencode
import json

from flask import Flask, redirect, url_for, render_template, flash, session, \
    current_app, request, abort
import requests

from flask import Flask, request, session, redirect, url_for, render_template
from cas import CASClient

app = Flask(__name__)

############### CAS THINGS #########################################################
app.secret_key = 'farooqa'
cas_client = CASClient(
    version=3,
    service_url = <serice-url>,
    server_url = <server-url>,
    verify_ssl_certificate=False
)

@app.route('/successful')
def successful():
    return redirect(url_for('index'))  # Redirect to the root page after successful login

@app.route('/login')
def login():
    if 'username' in session:
        # Already logged in
        return redirect(url_for('index'))

    next_url = request.args.get('next')
    ticket = request.args.get('ticket')
    if not ticket:
        # No ticket, the request comes from the end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        return redirect(cas_login_url)

    # There is a ticket, the request comes from CAS as callback.
    # Need to call `verify_ticket()` to validate ticket and get user profile.
    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

    if not user:
        return 'Failed to verify ticket. <a href="/login">Login</a>'
    else:  # Login successfully, redirect according to `next_url` query parameter.
        session['username'] = user
        return redirect(next_url or url_for('index'))  # Redirect to the next_url if provided, otherwise redirect to the root page

@app.route('/logout')
def logout():
    redirect_url = url_for('logout_callback', _external=True)
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    return redirect(cas_logout_url)

@app.route('/logout_callback')
def logout_callback():
    # Redirect from CAS logout request after CAS logout successfully
    session.pop('username', None)
    return 'Logged out from CAS. <a href="/login">Login</a>'


from functools import wraps

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorated_function

###########################################################################


####################### OAUTH #####################################

provider_data = {
'client_id': os.environ.get('TODOIST_CLIENT_ID'),
'client_secret': os.environ.get('TODOIST_CLIENT_SECRET'),
'authorize_url': 'https://todoist.com/oauth/authorize',
'token_url': 'https://todoist.com/oauth/access_token',
'scope': 'data:read'
}


@app.route('/authorize')
def oauth2_authorize():
    global provider_data

    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('oauth2_callback', _external=True),
        'response_type': 'code',
        'scope': provider_data['scope'],
        'state': session['oauth2_state'],
    })

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(provider_data['authorize_url'] + '?' + qs)


@app.route('/callback')
def oauth2_callback():

    global provider_data
    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('index'))

    # make sure that the state parameter matches the one we created in the
    # authorization request
    if request.args['state'] != session.get('oauth2_state'):
        abort(401)

    # make sure that the authorization code is present
    if 'code' not in request.args:
        abort(401)

    # exchange the authorization code for an access token
    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('oauth2_callback', _external=True),
    }, headers={'Accept': 'application/json'})

    if response.status_code != 200:
        abort(401)

    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
        abort(401)

    session['oauth2_token'] = oauth2_token
    flash(f'your token is {oauth2_token}')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=4400, ssl_context=('adhoc'))



#########################################################################


@app.route('/')
@login_required
def index():
    return '<h1> Apache Server</h1>'





if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", ssl_context='adhoc', port=5433)

