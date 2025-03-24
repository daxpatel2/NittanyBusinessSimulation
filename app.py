from pyexpat.errors import messages

from flask import Flask, render_template, request
from database_queries import fetch_user_data
app = Flask(__name__)


@app.route('/', methods=['GET','POST'])
def home_page():
    message = None
    if request.method == 'POST':
        # post request we need to read the incoming data and check it with the database, fields
        email = request.form['email']
        password = request.form['password']
        status = verify_login(email, password)
        if status:
            message = f"Welcome, {email}!"
        elif status == False:
            message = "Incorrect password"
        else:
            message = "User does not exist"
    return render_template('mainpage.html', message = message)


def verify_login(email, password):
    return fetch_user_data(email, password)

if __name__ == '__main__':
    app.run()
