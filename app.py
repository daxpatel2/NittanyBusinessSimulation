# app.py
from decimal import Decimal

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from database_queries import *

# create flask app instance
app = Flask(__name__)

app.secret_key = "super secret key"

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


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None

    # Only run this logic on POST
    if request.method == 'POST':
        email            = request.form['email']
        password         = request.form['password']
        confirm_password = request.form['confirm_password']
        role             = request.form['role']

        # 1) password check
        if password != confirm_password:
            message = "Passwords do not match. Please try again."
            return render_template('register.html', message=message)

        else:
            # 2) try to add new user
            created = add_user_to_database(email, password)
            if not created:
                message = f"An account with {email} already exists."
                return render_template('register.html', message=message)
            else:
                # 3) success → set up session & redirect
                session['email'] = email
                session['role']  = role

                # If you need to populate buyer/seller/helpdesk tables:
                conn, cursor = connect()
                if role == 'buyer':
                    cursor.execute(
                        "INSERT INTO buyer(email) VALUES (%s) ON CONFLICT DO NOTHING",
                        (email,)
                    )
                elif role == 'seller':
                    cursor.execute(
                        "INSERT INTO sellers(email) VALUES (%s) ON CONFLICT DO NOTHING",
                        (email,)
                    )
                conn.commit()
                cursor.close()
                conn.close()

                # redirect to the correct dashboard
                if role == "buyer":
                    return redirect(url_for('buyer'))
                elif role == "seller":
                    return redirect(url_for('seller'))
                else:
                    return redirect(url_for('helpdesk'))

    # GET or POST-with-error: render the form and show any message
    return render_template('register.html', message=message)

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

# Route for sellers to view and manage their own listings
@app.route('/seller/listings')
def manage_listings():
    # ensure only a seller can access this page
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))  # redirect others back home

    seller_email = session['email']  # get seller's email from session
    listings = get_listings_by_seller(seller_email)  # fetch listings from DB

    # fetch all currently active promotions for this seller
    conn, cursor = connect()
    cursor.execute("""
                   SELECT listing_id
                   FROM promotions
                   WHERE seller_email = %s
                   """, (seller_email,))
    promoted_ids = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    return render_template('seller_listings.html', listings=listings, promoted_ids=promoted_ids)  # render template with data


@app.route('/seller/listings/promote/<int:listing_id>', methods=['POST'])
def promote_listing(listing_id):
    # 1) ensure seller owns this listing
    seller_email = session.get('email')
    if session.get('role') != 'seller':
        flash("You’re not allowed to do that.", "danger")
        return redirect(url_for('manage_listings'))

    # 2) calculate fee and charge (replace with your real logic)
    conn, cursor = connect()
    cursor.execute(
        "SELECT product_price FROM product_listings "
        "WHERE seller_email=%s AND listing_id=%s",
        (seller_email, listing_id)
    )
    row = cursor.fetchone()
    if not row:
        flash("Listing not found.", "danger")
        cursor.close(); conn.close()
        return redirect(url_for('manage_listings'))

    price = row[0]
    fee = price * Decimal("0.05")

    # 3) insert promotion record
    try:
        cursor.execute(
          "INSERT INTO promotions (seller_email, listing_id, fee) "
          "VALUES (%s, %s, %s)",
          (seller_email, listing_id, fee)
        )
        conn.commit()
        flash("Your product is now promoted!", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("This product is already promoted.", "info")
    except Exception as e:
        conn.rollback()
        flash("Error promoting product.", "danger")
        print("Promote error:", e)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('manage_listings'))


# Route to create a new listing for the logged-in seller
@app.route('/seller/listings/new', methods=['GET','POST'])
def new_listing():
    # only sellers may add new listings
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    if request.method == 'POST':
        data = request.form  # get form data
        # call helper to insert listing into DB
        success = insert_product_listing(
            session['email'],
            data['category'], data['product_title'], data['product_name'],
            data['product_description'], int(data['quantity']), float(data['product_price'])
        )
        # show flash message on success or failure
        flash("Listing created" if success else "Error creating listing",
              "success" if success else "danger")
        return redirect(url_for('manage_listings'))  # back to listings view
    # GET request: show form with category options
    top_categories = get_subcategories('All')
    return render_template('seller_new_listing.html', categories=top_categories)


# Route to edit an existing listing identified by listing_id
@app.route('/seller/listings/edit/<int:listing_id>', methods=['GET','POST'])
def edit_listing(listing_id):
    # restrict to sellers
    if session.get('role') != 'seller':
        return redirect(url_for('home_page'))
    email = session['email']
    if request.method == 'POST':
        data = request.form  # form data for updates
        # update listing in DB
        success = update_product_listing(
            email, listing_id,
            data['category'], data['product_title'], data['product_name'],
            data['product_description'], int(data['quantity']), float(data['product_price'])
        )
        flash("Listing updated" if success else "Error updating listing",
              "success" if success else "danger")
        return redirect(url_for('manage_listings'))
    # GET: load existing listing to prefill form
    all_listings = get_listings_by_seller(email)
    # find matching listing tuple by ID
    listing = next((l for l in all_listings if l[0] == listing_id), None)
    return render_template('seller_edit_listing.html', listing=listing)


# Route to soft-delete (deactivate) a listing by setting its status to inactive (0)
@app.route('/seller/listings/remove/<int:listing_id>')
def remove_listing(listing_id):
    if session.get('role') != 'seller':
        flash("You must be a seller to remove a listing.", "danger")
        return redirect(url_for('home_page'))

    success = remove_product_listing(session['email'], listing_id)
    if success:
        flash("Listing removed successfully.", "warning")
    else:
        flash("Error removing listing.", "danger")
    return redirect(url_for('manage_listings'))


# Route to display category hierarchy and list products under a category
@app.route('/categories')
def categories():
    parent = request.args.get('parent', 'All')  # current category (default 'All')
    promoted = []
    if parent == "All":
        # 1) fetch promoted products
        promoted = get_promoted_listings()
        subcategories = get_subcategories(parent)  # fetch all top-level subcats
        products = []  # no direct products under 'All'
    else:
        subcategories = get_subcategories(parent)  # fetch subcategories of parent
        products = get_products_by_category(parent)  # fetch products for this category
    # render page with both lists
    return render_template('categories.html',
                           parent=parent,
                           subcategories=subcategories,
                           products=products,
                           promoted=promoted)


# Route to handle new orders (form and submission)
@app.route('/order/<seller_email>/<int:listing_id>', methods=['GET','POST'])
def order_form(seller_email, listing_id):
    buyer = session.get('email')
    # only buyers may place orders
    if session.get('role')!='buyer' or not buyer:
        return redirect(url_for('home_page'))
    # fetch product details or show error if not found
    prod = get_product_details(seller_email, listing_id)
    if not prod:
        flash("product not found", "danger")
        return redirect(url_for('categories'))
    cards = get_credit_cards_by_buyer(buyer)  # fetch saved cards
    if request.method=='POST':
        qty = int(request.form['quantity'])  # requested quantity
        card_choice = request.form.get('card_choice')
        if card_choice=='new':  # adding a new card
            cc = request.form['cc_num']
            ctype = request.form['cc_type']
            em = int(request.form['cc_month'])
            ey = int(request.form['cc_year'])
            sc = request.form['cc_cvc']
            add_credit_card(cc, ctype, em, ey, sc, buyer)  # save new card
            chosen = cc
        else:
            chosen = card_choice  # use existing card
        # attempt to insert order and update inventory
        success = insert_order(seller_email, listing_id, buyer, qty, chosen)
        flash("order placed successfully" if success else "order failed",
              "success" if success else "danger")
        return redirect(url_for('orders'))
    # GET: show order form
    return render_template(
        'order_form.html',
        product=prod,
        cards=cards
    )


# Alternative checkout route, consolidating order and payment details
@app.route('/checkout/<seller_email>/<int:listing_id>', methods=['GET','POST'])
def checkout(seller_email, listing_id):
    # ensure only buyers
    if session.get('role') != 'buyer':
        return redirect(url_for('home_page'))

    product = get_product_details(seller_email, listing_id)  # fetch product
    cards = get_credit_cards_by_buyer(session['email'])  # fetch buyer's cards

    if request.method == 'POST':
        qty = int(request.form['quantity'])  # get quantity
        cc  = request.form['credit_card_num']  # selected card
        # call insert_order with correct param order
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
    # GET: render checkout page
    return render_template('checkout.html',
                           product=product,
                           cards=cards)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    email = session['email']
    conn, cursor = connect()

    # Fetch current profile info (excluding password!)
    cursor.execute("""
      SELECT *
        FROM users
       WHERE email = %s
    """, (email,))
    user = cursor.fetchone() or (None, None, None)
    cursor.close()
    conn.close()

    if request.method == 'POST':
        new_password  = request.form['new_password']
        confirm_pw    = request.form['confirm_password']
        hashed = None

        # 1) If they typed a new password, make sure it matches
        if new_password:
            if new_password != confirm_pw:
                flash("Passwords don’t match.", "error")
                return render_template('profile.html',
                           email=email)
            hashed = hash_password(new_password)

        # 2) Build your UPDATE statement dynamically
        updates = []
        params  = []

        if hashed:
            updates.append("password = %s")
            params.append(hashed)

        # nothing to do?
        if updates:
            sql = "UPDATE users SET " + ", ".join(updates) + " WHERE email = %s"
            params.append(email)

            conn, cursor = connect()
            cursor.execute(sql, tuple(params))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Profile updated!", "success")

        return redirect(url_for('profile'))

    # GET → render form with existing values
    return render_template('profile.html',
                           email=email)



# Route to show product details, including seller's average rating
@app.route('/product/<seller_email>/<int:listing_id>')
def product_detail(seller_email, listing_id):
    product = get_product_details(seller_email, listing_id)  # fetch details
    if product is None:
        flash("product not found")
        return redirect(url_for('categories') + '?parent=All')
    avg_rating = get_seller_average_rating(seller_email)  # compute avg review score
    return render_template(
        'product_detail.html',
        product=product,
        avg_rating=avg_rating
    )


# Route for buyers to submit reviews on their orders
@app.route('/review/<int:order_id>', methods=['GET','POST'])
def review(order_id):
    # only buyers may review
    if session.get('role') != 'buyer':
        return redirect(url_for('home_page'))

    buyer = session['email']
    # get all orders for this buyer
    my_orders = get_orders_by_buyer(buyer)
    # find matching order tuple
    order = next((o for o in my_orders if o[0] == order_id), None)
    if not order:
        flash("order not found", "danger")
        return redirect(url_for('orders'))

    # extract seller and listing to label the product
    seller_email, listing_id = order[2], order[3]
    product = get_product_details(seller_email, listing_id)
    product_label = f"{product[3]} – {product[4]}"  # "title – name"

    if request.method == 'POST':
        rating = int(request.form['rating'])  # get rating value
        review_desc = request.form['review_desc']  # review text
        success = insert_review(order_id, review_desc, rating)  # upsert review
        flash("Review submitted!" if success else "Error submitting review",
              "success" if success else "danger")
        return redirect(url_for('orders'))

    # GET: show review form
    return render_template('review_form.html',
                           order_id=order_id,
                           product_label=product_label)


# Route to display past orders with seller ratings included
@app.route('/orders')
def orders():
    buyer = session.get('email')
    # restrict to buyers
    if session.get('role') != 'buyer' or not buyer:
        return redirect(url_for('home_page'))

    raw_orders = get_orders_by_buyer(buyer)  # fetch orders
    orders_with_rating = []
    # append average seller rating to each order tuple
    for order in raw_orders:
        seller_email = order[2]
        avg = get_seller_average_rating(seller_email)
        orders_with_rating.append((*order, avg))
    return render_template('orders.html', orders=orders_with_rating)  # render orders page


# New route for product search functionality
@app.route('/search')
def search_products_route():
    # Get search parameters from request
    keywords = request.args.get('keywords', '')
    min_price_str = request.args.get('min_price', '')
    max_price_str = request.args.get('max_price', '')
    sort_by = request.args.get('sort_by', 'relevance')

    # Convert price strings to float if provided
    min_price = float(min_price_str) if min_price_str else None
    max_price = float(max_price_str) if max_price_str else None

    # Determine if a search was performed
    search_performed = bool(keywords or min_price is not None or max_price is not None)

    # Perform search using the database query function
    products = search_products(keywords, min_price, max_price, sort_by) if search_performed else []

    # Render the search results template
    return render_template('search_result.html',
                           products=products,
                           search_performed=search_performed)

# main driver to run flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)