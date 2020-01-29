#! /usr/bin/env python3
# By Anmar Al_fallahi
import os
import requests
import string
import random
import json
import httplib2
from flask import Flask, render_template, request,\
    redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session, make_response
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogDB.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# client Id by json
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# JSON APIs to view Category Information
@app.route('/catalog.JSON')
def catalogJSON():
    items = session.query(CategoryItem).all()
    return jsonify(Category=[item.serialize for item in items])


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('\
        Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:\
     150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/')
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show all Categories and Items
@app.route('/')
@app.route('/category/')
def showCategory():
    categories = session.query(Category).all()
    items = session.query(CategoryItem).order_by(desc(CategoryItem.id))
    if'username' not in login_session:
        return render_template('category.html',
                               categories=categories, items=items,
                               login_session=login_session)
    if session.query(User).filter_by(id=login_session['user_id']):
        items = session.query(CategoryItem).filter_by(
            user_id=login_session['user_id']).order_by(desc(CategoryItem.id))
        return render_template('category_private.html', categories=categories,
                               items=items, login_session=login_session)
    return "some errors happened "


# Show all Items
@app.route('/category/<string:name>/Items')
def showItems(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).first()
    items = session.query(CategoryItem).filter_by(category_id=category.id)
    count = session.query(CategoryItem).filter_by(
        category_id=category.id).count()
    if 'username' not in login_session:
        return render_template('item.html', categories=categories,
                               category=category, items=items,
                               count=count, login_session=login_session)
    if session.query(User).filter_by(id=login_session['user_id']):
        return render_template('item_private.html', categories=categories,
                               category=category, items=items,
                               count=count, login_session=login_session)
    return "some errors were happened "


# Show Description as normal user not as logged user
@app.route('/category/<string:category>/<string:item>/')
def showDescription(category, item):
    category = session.query(Category).filter_by(name=category).first()
    item = session.query(CategoryItem).filter_by(name=item).first()
    if item:
        return render_template('description.html', item=item)
    return "Please choose correct info"


# Create new Item
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    if session.query(User).filter_by(id=login_session['user_id']):
        if request.method == 'POST':
            user = session.query(User).filter_by(
                name=login_session['username']).one()
            category = session.query(Category).filter_by(name=request.form[
                'category']).one()
            if request.form['name'] == '':
                return render_template('newItem.html\
                        ', categories=categories, login_session=login_session)
            newItem = CategoryItem(name=request.form['name\
                                                     '], description=request.form['description\
            '], category_id=category.id, category=category, user=user,
                                   user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            flash('New %s Item Successfully Created' % (newItem.name))
            return redirect(url_for('showCategory'))
        else:
            return render_template('newItem.html', categories=categories,
                                   login_session=login_session)


# Show Item information.
@app.route('/catalog/<string:category>/<string:item>/',
           methods=['GET', 'POST'])
def itemInfo(category, item):
    if session.query(Category).filter_by(name=category).first():
        item = session.query(CategoryItem).filter_by(name=item).first()
        if item:
            return render_template('itemInfo.html',
                                   item=item, login_session=login_session)
    return 'Please choose correct data.'


# Edit Item
@app.route('/catalog/<string:itemname>/edit/', methods=['GET', 'POST'])
def editItem(itemname):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(name=itemname).first()
    categories = session.query(Category).all()
    if session.query(User).filter_by(id=login_session['user_id']):
        if request.method == 'POST':
            category = session.query(Category).filter_by(
                name=request.form['category']).one()
            if request.form['name']:
                item.name = request.form['name']
            if request.form['description']:
                item.description = request.form['description']
            if request.form['category']:
                item.category = category
            session.add(item)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('showCategory'))
        else:
            return render_template('edititem.html', categories=categories,
                                   item=item, login_session=login_session)
            print('you are in:')


# Delete an item
@app.route('/catalog/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    item = session.query(CategoryItem).filter_by(name=item_name).first()
    if session.query(User).filter_by(id=login_session['user_id']):
        if request.method == 'POST':
            session.delete(item)
            session.commit()
            flash('Menu Item Successfully Deleted')
            return redirect(url_for('showCategory'))
        else:
            return render_template('deleteitem.html', categories=categories,
                                   item=item, login_session=login_session)


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


# get user information by using user_id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# get user ID by using email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# this context_processor and dated_url_for function used for updating pages
# when css file updated
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


# this is the main function when this file running
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
