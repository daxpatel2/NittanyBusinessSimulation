# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from database_queries import (
    fetch_user_data, get_user_role,
    get_subcategories, get_products_by_category, get_product_details,
    get_listings_by_seller, insert_product_listing,
    update_product_listing, set_listing_status,
    get_orders_by_buyer, get_credit_cards_by_buyer,
    insert_order, add_credit_card
)

# create flask app instance
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # needed for session management and flashing

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
        status = fetch_user_data(email, password)

        # if user exists and password is correct
        if status:
            # get role of user from database
            role = get_user_role(email)
            # record user info in session
            session['email'] = email
            session['role'] = role

            # redirect user to their respective dashboard based on role
            if role == "buyer":
                return redirect(url_for('buyer'))
            elif role == "seller":
                return redirect(url_for('seller'))
            elif role == "helpdesk":
                return redirect(url_for('helpdesk'))
            else:
                # fallback message if role doesn't match any known role
                message = f"Welcome, {email}! (role not defined)"

        # if user exists but password is incorrect
        elif status is False:
            message = "Incorrect password"

        # if user does not exist in database
        else:
            message = "User does not exist"

    # render login page template with message variable
    return render_template('mainpage.html', message=message)

# simple logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home_page'))

# route for buyer dashboard
@app.route('/buyer')
def buyer():
    # ensure only buyers can access
    if session.get('role') != 'buyer':
        return redirect(url_for('home_page'))
    # render buyer dashboard template with email variable
    return render_template('buyers.html', email=session['email'])

# route for seller dashboard
@app.route('/seller')
def seller():
    # ensure only sellers can access
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    # render seller dashboard template with email variable
    return render_template('sellers.html', email=session['email'])

# route for helpdesk dashboard
@app.route('/helpdesk')
def helpdesk():
    # ensure only helpdesk staff can access
    if session.get('role') != 'helpdesk':
        return redirect(url_for('home_page'))
    # render helpdesk dashboard template with email variable
    return render_template('helpdesk_staff.html', email=session['email'])

@app.route('/seller/listings')
def manage_listings():
    # only seller can manage their listings
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    seller_email = session['email']
    listings = get_listings_by_seller(seller_email)
    return render_template('seller_listings.html', listings=listings)

@app.route('/seller/listings/new', methods=['GET','POST'])
def new_listing():
    # only seller can add new listing
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    if request.method == 'POST':
        data = request.form
        success = insert_product_listing(
            session['email'],
            data['category'], data['product_title'], data['product_name'],
            data['product_description'], int(data['quantity']), float(data['product_price'])
        )
        flash("Listing created" if success else "Error creating listing",
              "success" if success else "danger")
        return redirect(url_for('manage_listings'))
    top_categories = get_subcategories('All')
    return render_template('seller_new_listing.html', categories=top_categories)

@app.route('/seller/listings/edit/<int:listing_id>', methods=['GET','POST'])
def edit_listing(listing_id):
    # only seller can edit their listings
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    email = session['email']
    if request.method == 'POST':
        data = request.form
        success = update_product_listing(
            email, listing_id,
            data['category'], data['product_title'], data['product_name'],
            data['product_description'], int(data['quantity']), float(data['product_price'])
        )
        flash("Listing updated" if success else "Error updating listing",
              "success" if success else "danger")
        return redirect(url_for('manage_listings'))
    # GET: prefill form with existing data
    listing = next((l for l in get_listings_by_seller(email) if l[0] == listing_id), None)
    return render_template('seller_edit_listing.html', listing=listing)

@app.route('/seller/listings/remove/<int:listing_id>')
def remove_listing(listing_id):
    # only seller can remove their listings
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    success = set_listing_status(session['email'], listing_id, 0)
    flash("Listing removed" if success else "Error removing listing",
          "warning" if success else "danger")
    return redirect(url_for('manage_listings'))

# route to dynamically display category hierarchy and products
@app.route('/categories')
def categories():
    parent = request.args.get('parent', 'All')
    if parent == "All":
        subcategories = get_subcategories(parent)
        products = []  # "All" does not have products directly
    else:
        subcategories = get_subcategories(parent)
        products = get_products_by_category(parent)
    return render_template('categories.html',
                           parent=parent,
                           subcategories=subcategories,
                           products=products)

# route to display product details dynamically
@app.route('/product/<seller_email>/<int:listing_id>')
def product_detail(seller_email, listing_id):
    product = get_product_details(seller_email, listing_id)
    if product is None:
        flash("product not found")
        return redirect(url_for('categories') + '?parent=All')
    return render_template('product_detail.html', product=product)

@app.route('/order/<seller_email>/<int:listing_id>', methods=['GET','POST'])
def order_form(seller_email, listing_id):
    buyer = session.get('email')
    if session.get('role')!='buyer' or not buyer:
        return redirect(url_for('home_page'))
    prod = get_product_details(seller_email, listing_id)
    if not prod:
        flash("product not found", "danger")
        return redirect(url_for('categories'))
    cards = get_credit_cards_by_buyer(buyer)
    if request.method=='POST':
        qty = int(request.form['quantity'])
        card_choice = request.form.get('card_choice')
        if card_choice=='new':
            cc = request.form['cc_num']
            ctype = request.form['cc_type']
            em = int(request.form['cc_month'])
            ey = int(request.form['cc_year'])
            sc = request.form['cc_cvc']
            add_credit_card(cc, ctype, em, ey, sc, buyer)
            chosen = cc
        else:
            chosen = card_choice
        success = insert_order(seller_email, listing_id, buyer, qty, chosen)
        flash("order placed successfully" if success else "order failed", "success" if success else "danger")
        return redirect(url_for('orders'))
    return render_template(
        'order_form.html',
        product=prod,
        cards=cards
    )

@app.route('/orders')
def orders():
    buyer = session.get('email')
    if session.get('role')!='buyer' or not buyer:
        return redirect(url_for('home_page'))
    my_orders = get_orders_by_buyer(buyer)
    return render_template('orders.html', orders=my_orders)

@app.route('/checkout/<seller_email>/<int:listing_id>', methods=['GET','POST'])
def checkout(seller_email, listing_id):
    # ensure buyer is logged in
    if session.get('role') != 'buyer':
        return redirect(url_for('home_page'))

    product = get_product_details(seller_email, listing_id)
    cards = get_credit_cards_by_buyer(session['email'])

    if request.method == 'POST':
        qty = int(request.form['quantity'])
        cc  = request.form['credit_card_num']

        # pass args in the correct order:
        # seller_email, listing_id, buyer_email, quantity, credit_card_num
        success = insert_order(
            seller_email,
            listing_id,
            session['email'],
            qty,
            cc
        )

        if success:
            flash("Order placed successfully!", "success")
            return redirect(url_for('orders'))
        else:
            flash("Error placing order", "danger")

    # GET: render the checkout form
    return render_template('checkout.html',
                           product=product,
                           cards=cards)
# main driver to run flask app
if __name__ == '__main__':
    # run flask app with debug mode on (shows detailed error logs in browser)
    app.run(debug=True)
