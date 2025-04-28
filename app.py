from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from database_queries import *
from decimal import Decimal

# create flask app instance
app = Flask(__name__)
app.secret_key = "secret_key"  # needed for session management and flashing

@app.route('/', methods=['GET', 'POST'])
def mainpage():
    message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        status = fetch_user_data(email, password)
        if status:
            role = get_user_role(email)
            session['email'] = email
            session['role'] = role
            if role == "buyer":
                return redirect(url_for('buyer'))
            elif role == "seller":
                return redirect(url_for('seller'))
            elif role == "helpdesk":
                return redirect(url_for('helpdesk'))
            else:
                message = f"Welcome, {email}! (role not defined)"
        elif status is False:
            message = "Incorrect password"
        else:
            message = "User does not exist"
    return render_template('mainpage.html', message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        if password != confirm_password:
            message = "Passwords do not match. Please try again."
            return render_template('register.html', message=message)
        else:
            created = add_user_to_database(email, password)
            if not created:
                message = f"An account with {email} already exists."
                return render_template('register.html', message=message)
            else:
                session['email'] = email
                session['role'] = role
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
                if role == "buyer":
                    return redirect(url_for('buyer'))
                elif role == "seller":
                    return redirect(url_for('seller'))
                else:
                    return redirect(url_for('helpdesk'))
    return render_template('register.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('mainpage'))

@app.route('/buyer')
def buyer():
    if session.get('role') != 'buyer':
        return redirect(url_for('mainpage'))
    return redirect(url_for('buyer_home'))

@app.route('/buyer_home')
def buyer_home():
    if session.get('role') != 'buyer':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))

    # Handle search form submission and category selection
    keywords = request.args.get('keywords', '')
    min_price_str = request.args.get('min_price', '')
    max_price_str = request.args.get('max_price', '')
    sort_by = request.args.get('sort_by', 'relevance')
    category = request.args.get('category', 'All')  # Default to 'All' if no category is selected
    min_price = float(min_price_str) if min_price_str else None
    max_price = float(max_price_str) if max_price_str else None

    # Get the category navigation path (e.g., ['All', 'Clothing', 'Bottoms'])
    path = request.args.getlist('path')
    if not path:
        path = ['All']  # Initial state: start at "All"

    # Fetch products if a category is selected (except "All") or other filters are applied
    search_performed = bool(keywords or min_price is not None or max_price is not None or (category and category != 'All'))
    products = search_products(keywords, min_price, max_price, sort_by, category) if search_performed else []

    return render_template('buyer_home.html',
                           email=email,
                           products=products,
                           search_performed=search_performed,
                           selected_category=category,
                           path=path,
                           get_subcategories=get_subcategories)

@app.route('/seller')
def seller():
    if session.get('role') != 'seller':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    listings = get_listings_by_seller(email)
    return render_template('seller_home.html', email=email, listings=listings)

@app.route('/helpdesk')
def helpdesk():
    if session.get('role') != 'helpdesk':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    return render_template('helpdesk_home.html', email=email)

@app.route('/helpdesk/pending_requests')
def pending_requests():
    if session.get('role') != 'helpdesk':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    return render_template('pending_requests.html', email=email)

@app.route('/helpdesk/user_management')
def user_management():
    if session.get('role') != 'helpdesk':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    return render_template('user_management.html', email=email)

@app.route('/helpdesk/system_admin')
def system_admin():
    if session.get('role') != 'helpdesk':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    return render_template('system_admin.html', email=email)

# @app.route('/seller/listings')
# def manage_listings():
#     if session.get('role') != 'seller':
#         return redirect(url_for('mainpage'))
#     return redirect(url_for('seller'))

@app.route('/seller/listings')
def manage_listings():
    # ensure only a seller can access this page
    if session.get('role') != 'seller':
        return redirect(url_for('mainpage'))  # redirect others back home

    seller_email = session['email']  # get seller's email from session
    listings = get_listings_by_seller(seller_email)  # fetch listings from DB

    # fetch all currently active promotions for this seller
    conn, cursor = connect()
    # cursor.execute("""
    #                SELECT listing_id
    #                FROM promotions
    #                WHERE seller_email = %s
    #                """, (seller_email,))
    # promoted_ids = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    return render_template('seller_listings.html', listings=listings)  # render template with data
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



@app.route('/seller/listings/edit/<int:listing_id>', methods=['GET','POST'])
def edit_listing(listing_id):
    if session.get('role') != 'seller':
        return redirect(url_for('mainpage'))
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
    all_listings = get_listings_by_seller(email)
    listing = next((l for l in all_listings if l[0] == listing_id), None)
    return render_template('seller_edit_listing.html', listing=listing)

@app.route('/seller/listings/remove/<int:listing_id>')
def remove_listing(listing_id):
    if session.get('role') != 'seller':
        return redirect(url_for('mainpage'))
    success = remove_listing(session['email'], listing_id)
    flash("Listing removed" if success else "Error removing listing",
          "warning" if success else "danger")
    return redirect(url_for('manage_listings'))

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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Ensure user is logged in
    email = session.get('email')
    if not email:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for('mainpage'))

    role = session.get('role')
    # Determine template based on role
    template = 'profile.html' if role == 'buyer' else 'profile_nonbuyer.html'

    # Fetch current profile info (excluding password!)
    conn, cursor = connect()
    if conn is None or cursor is None:
        flash("Database connection failed. Please try again later.", "error")
        return render_template(template, email=email, role=role)

    try:
        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone() or (None, None, None)
    except Exception as e:
        flash("Error fetching user data. Please try again later.", "error")
        print(f"Error fetching user data for {email}: {e}")
        cursor.close()
        conn.close()
        return render_template(template, email=email, role=role)
    finally:
        cursor.close()
        conn.close()

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_pw = request.form['confirm_password']
        hashed = None

        # If they typed a new password, make sure it matches
        if new_password:
            if new_password != confirm_pw:
                flash("Passwords don’t match.", "error")
                return render_template(template, email=email, role=role)
            hashed = hash_password(new_password)

        # Build UPDATE statement dynamically
        updates = []
        params = []

        if hashed:
            updates.append("password = %s")
            params.append(hashed)

        # If there are updates, execute them
        if updates:
            sql = "UPDATE users SET " + ", ".join(updates) + " WHERE email = %s"
            params.append(email)

            conn, cursor = connect()
            if conn is None or cursor is None:
                flash("Database connection failed. Please try again later.", "error")
                return render_template(template, email=email, role=role)

            try:
                cursor.execute(sql, tuple(params))
                conn.commit()
                flash("Profile updated!", "success")
            except Exception as e:
                flash("Error updating profile. Please try again later.", "error")
                print(f"Error updating profile for {email}: {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

            return redirect(url_for('profile'))
        else:
            # If no changes were made, re-render the page with a message
            flash("No changes made.", "info")
            return render_template(template, email=email, role=role)

    # GET → render form with existing values
    return render_template(template, email=email, role=role)



@app.route('/product/<seller_email>/<int:listing_id>')
def product_detail(seller_email, listing_id):
    if session.get('role') != 'buyer':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    product = get_product_details(seller_email, listing_id)
    if product is None:
        flash("product not found")
        return redirect(url_for('buyer_home'))
    avg_rating = get_seller_average_rating(seller_email)
    return render_template(
        'product_detail.html',
        email=email,
        product=product,
        avg_rating=avg_rating
    )

@app.route('/review/<int:order_id>', methods=['GET','POST'])
def review(order_id):
    # only buyers may review
    if session.get('role') != 'buyer':
        return redirect(url_for('mainpage'))

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
@app.route('/shopping_cart')
def shopping_cart():
    if session.get('role') != 'buyer':
        return redirect(url_for('mainpage'))
    email = session.get('email')
    if not email:
        return redirect(url_for('mainpage'))
    return render_template('shopping_cart.html', email=email)


@app.route('/orders')
def orders():
    buyer = session.get('email')
    if session.get('role') != 'buyer' or not buyer:
        return redirect(url_for('mainpage'))
    raw_orders = get_orders_by_buyer(buyer)
    orders_with_rating = []
    for order in raw_orders:
        seller_email = order[2]
        try:
            avg = get_seller_average_rating(seller_email)
        except Exception as e:
            print(f"Error calculating average rating for {seller_email}: {e}")
            avg = None
        orders_with_rating.append((*order, avg))
    return render_template('orders.html', orders=orders_with_rating)

if __name__ == '__main__':
    app.run(debug=True)
