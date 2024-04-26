import identity.web
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
import app_config
import json

app = Flask(__name__)
app.config.from_object(app_config)
assert app.config["REDIRECT_PATH"] != "/", "REDIRECT_PATH must not be /"
Session(app)

# Creating auth object with variables from app_config.py
auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)

@app.route("/login")
def login():
    return render_template("login.html", **auth.log_in(
        scopes = app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri = url_for("auth_response", _external=True),
        prompt="select_account"
        ))

@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    # Redirect to login page after logout
    return redirect(auth.log_out(url_for("index", _external=True)))

@app.route("/")
def index():
    if not auth.get_user(): # If not logged, in redirect to login page
        return redirect(url_for("login"))
    
    # If logged in, show homepage
    return render_template('index.html', user=auth.get_user())


@app.route("/profile", methods=["GET"])
def get_profile():
    user = auth.get_user() # Check if logged in

    if not user: # If not, redirect to error page.
        error = "401 Unauthorized"
        error_description = "You need to be logged in to access this page."
        result = {"error": error, "error_description": error_description}
        return render_template("auth_error.html", result=result)
    
    token = auth.get_token_for_user(app_config.SCOPE)

    # If the user is logged in, request the profile
    result = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': 'Bearer ' + token['access_token']}
    )

    if result.status_code == 200: 

        profile_data = result.json() # Get profile data
        return render_template('profile.html', user=profile_data, result=result)
    
    # Error handling
    else:
        error = result.status_code
        error_description = "Error accessing profile."
        result = {"error": error, "error_description": error_description}
        return render_template("auth_error.html", result=result)


@app.route("/profile", methods=["POST"])
def post_profile():
    # Check if the user is logged in
    user = auth.get_user()

    # If not logged in, redirect to error page
    if not user: 
        error = "401 Unauthorized"
        error_description = "You need to be logged in to access this page."
        result = {"error": error, "error_description": error_description}
        return render_template("auth_error.html", result=result)
    
    # If logged in, get token
    token = auth.get_token_for_user(app_config.SCOPE)

    # Construct the request headers with the access token
    headers = {
        "Authorization": "Bearer " + token['access_token'],
        "Content-Type": "application/json"
    }

    # Construct the request body with the data to update the user's profile
    body = {
        "mobilePhone": request.form.get("mobilePhone"),
        "businessPhones": [request.form.get("businessPhone")]
    }

    # Send the request
    result = requests.patch('https://graph.microsoft.com/v1.0/users/' + request.form.get("id"), 
                            headers=headers, 
                            json=body)
    
    if result.status_code == 204:
        profile = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': 'Bearer ' + token['access_token']}
        )
        return render_template('profile.html', user=profile.json(), result=None)
    
    # Error handling
    else:
        error_info = json.loads(result.text)
        error = error_info["error"]["code"]
        error_description = error_info["error"]["message"] 
        result = {"error": result.status_code, "error_description": error_description}
        return render_template("auth_error.html", result=result)


@app.route("/users")
def get_users():

    user = auth.get_user() # Check if logged in

    if not user: # If not, redirect to error page.
        error = "401 Unauthorized"
        error_description = "You need to be logged in to access this page."
        result = {"error": error, "error_description": error_description}
        return render_template("auth_error.html", result=result)
    
    # Send request
    token = auth.get_token_for_user(app_config.SCOPE)
    result = requests.get(
        'https://graph.microsoft.com/v1.0/users',
        headers={'Authorization': 'Bearer ' + token['access_token']}
    )

    if result.status_code == 200:
        return render_template('users.html', result=result.json())
    
    # Error handling
    else:
        error = result.status_code + result.text["error"]["code"]
        error_description = result.text["error"]["message"]

        result = {"error": error, "error_description": error_description}
        return render_template("auth_error.html", result=result)


if __name__ == "__main__":
    app.run()
