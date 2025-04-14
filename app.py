from flask import Flask, render_template, request, redirect, url_for
from database_queries import get_user_role, fetch_user_data

# create flask app instance
app = Flask(__name__)

# route for home page login
@app.route('/', methods=['GET', 'POST'])
def home_page():
    # message variable to store error or success messages for login
    message = None

    # check if form is submitted
    if request.method == 'POST':
        # get email and password values from the form
        email = request.form['email']
        password = request.form['password']

        # verify login credentials using helper function
        status = verify_login(email, password)

        # if user exists and password is correct
        if status:
            # get role of user from database
            role = get_user_role(email)

            # redirect user to their respective dashboard based on role
            if role == "buyer":
                return redirect(url_for('buyer', email=email))
            elif role == "seller":
                return redirect(url_for('seller', email=email))
            elif role == "helpdesk":
                return redirect(url_for('helpdesk', email=email))
            else:
                # fallback message if role doesn't match any known role
                message = f"Welcome, {email}! (role not defined)"

        # if user exists but password is incorrect
        elif status == False:
            message = "Incorrect password"

        # if user does not exist in database
        else:
            message = "User does not exist"

    # render login page template with message variable
    return render_template('mainpage.html', message=message)


# helper function to verify login credentials using fetch_user_data from database_queries.py
def verify_login(email, password):
    # returns True if login successful, False if wrong password, None if user doesn't exist
    return fetch_user_data(email, password)


# route for buyer dashboard
@app.route('/buyer')
def buyer():
    # get email from request arguments to display in dashboard
    email = request.args.get('email', '')
    # render buyer dashboard template with email variable
    return render_template('buyers.html', email=email)


# route for seller dashboard
@app.route('/seller')
def seller():
    # get email from request arguments to display in dashboard
    email = request.args.get('email', '')
    # render seller dashboard template with email variable
    return render_template('sellers.html', email=email)


# route for helpdesk dashboard
@app.route('/helpdesk')
def helpdesk():
    # get email from request arguments to display in dashboard
    email = request.args.get('email', '')
    # render helpdesk dashboard template with email variable
    return render_template('helpdesk_staff.html', email=email)


# main driver to run flask app
if __name__ == '__main__':
    # run flask app with debug mode on (shows detailed error logs in browser)
    app.run(debug=True)
