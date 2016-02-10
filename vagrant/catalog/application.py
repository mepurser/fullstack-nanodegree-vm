import os, random, string, json, requests, httplib2

from flask import Flask, render_template, request, make_response, redirect, jsonify, url_for, flash

#'session' is already used as db session, so renaming
# authentication session to 'login_session'
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import scoped_session, sessionmaker

from database_setup import Base, EquipCategory, EquipBrand, User

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'PV Equipment App'

databaseName = 'pv_equipment.db'
engine = create_engine('sqlite:///' + databaseName)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    #login_session['credentials'] = credentials
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

    # see if user exists, if not, make a new one
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ') 
    print(login_session['username'])
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token'] 
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected... redirecting...'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/index')
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# add new category page
@app.route('/index/new/', methods=['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = EquipCategory(
            name=request.form['name'], 
            user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        brands = session.query(EquipBrand).all()
        categories = session.query(EquipCategory).all()
        return render_template('new_category.html', 
            categories=categories, 
            brands=brands)
    else:
        brands = session.query(EquipBrand).all()
        categories = session.query(EquipCategory).all()
        return render_template('new_category.html', 
            categories=categories, 
            brands=brands)

# add new brand page
@app.route('/index/new/<int:category_id>', methods=['GET','POST'])
def newBrand(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newBrand = EquipBrand(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            user_id=login_session['user_id'])
        session.add(newBrand)
        session.commit()
        brands = session.query(EquipBrand).filter_by(category_id=category_id).all()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        return render_template('new_brand.html', curCategory=curCategory, brands=brands)
    else:
        brands = session.query(EquipBrand).filter_by(category_id=category_id).all()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        return render_template('new_brand.html', 
            curCategory=curCategory, 
            brands=brands)

# collect edits for existing brand
@app.route('/index/edit/inputs/<int:category_id>/<int:brand_id>', methods=['GET','POST'])
def inputEditsBrand(category_id, brand_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        curBrand = session.query(EquipBrand).filter_by(id=brand_id).first()
        if curBrand.user_id == curUser.id:
            return render_template('edit_brand.html', 
                curCategory=curCategory, 
                curBrand=curBrand)
        else:
            return render_template('unauthorized.html')

# collect edits for existing brand
@app.route('/index/edit/inputs/<int:category_id>', methods=['GET','POST'])
def inputEditsCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        if curCategory.user_id == curUser.id:
            return render_template('edit_category.html', 
                curCategory=curCategory)
        else:
            return render_template('unauthorized.html')

# edit existing brand
@app.route('/index/edit/confirmed/<int:category_id>/<int:brand_id>', methods=['GET','POST'])
def editBrand(category_id, brand_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        curBrand = session.query(EquipBrand).filter_by(id=brand_id).first()
        if curBrand.user_id == curUser.id:
            if request.method == 'POST':
                editedItem = session.query(EquipBrand).filter_by(id=brand_id).one()
                editedItem.name = request.form['name']
                editedItem.description = request.form['description']
                session.add(editedItem)
                session.commit()
                return redirect('/pv_equipment/' + str(category_id) + '/')
            else:
                return redirect('/index')
        else:
            return render_template('unauthorized.html')

# edit existing category
@app.route('/index/edit/confirmed/<int:category_id>', methods=['GET','POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        if curCategory.user_id == curUser.id:
            if request.method == 'POST':
                editedItem = session.query(EquipCategory).filter_by(id=category_id).one()
                editedItem.name = request.form['name']
                session.add(editedItem)
                session.commit()
                return redirect('/index')
            else:
                return redirect('/index')
        else:
            return render_template('unauthorized.html')

# confirm deletion of existing category
@app.route('/index/delete/<int:category_id>')
def delConfCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        if curCategory.user_id == curUser.id:
            return render_template('confirm_delete_category.html', 
                curCategory=curCategory)
        else:
            return render_template('unauthorized.html')

# confirm deletion of existing brand
@app.route('/index/delete/<int:category_id>/<int:brand_id>')
def delConfBrand(category_id, brand_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        curBrand = session.query(EquipBrand).filter_by(id=brand_id).first()
        if curBrand.user_id == curUser.id:
            return render_template('confirm_delete_brand.html', 
                curCategory=curCategory, 
                curBrand=curBrand)
        else:
            return render_template('unauthorized.html')

# delete existing brand
@app.route('/index/delete/confirmed/<int:category_id>/<int:brand_id>', methods=['GET','POST'])
def delBrand(category_id, brand_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curBrand = session.query(EquipBrand).filter_by(id=brand_id).first()
        if curBrand.user_id == curUser.id:
            if request.method == 'POST':
                itemToDelete = session.query(EquipBrand).filter_by(id=brand_id).one()
                session.delete(itemToDelete)
                session.commit()
                return redirect('/pv_equipment/' + str(category_id) + '/')
            else:
                return redirect('/pv_equipment/' + str(category_id) + '/')
        else:
            return render_template('unauthorized.html')

# delete existing category and all associated brands
@app.route('/index/delete/confirmed/<int:category_id>', methods=['GET','POST'])
def delCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        curUser = session.query(User).filter_by(name=login_session['username']).one()
        curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
        if curCategory.user_id == curUser.id:
            if request.method == 'POST':
                itemToDelete = session.query(EquipCategory).filter_by(id=category_id).one()
                session.delete(itemToDelete)
                brandsToDelete = session.query(EquipBrand).filter_by(category_id=category_id).all()
                for i in brandsToDelete:
                    session.delete(i)
                session.commit()
                return redirect('/index')
            else:
                return redirect('/index')
        else:
            return render_template('unauthorized.html')

# once category is clicked, list brands in second panel
@app.route('/pv_equipment/<int:category_id>/')
def showBrands(category_id):
    brands = session.query(EquipBrand).filter_by(category_id=category_id)
    curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
    categories = session.query(EquipCategory).all()
    userIsLoggedIn = False
    if 'username' in login_session:
        userIsLoggedIn = True
        user = session.query(User).filter_by(name=login_session['username']).one()
        return render_template('index.html', 
            curCategory=curCategory, 
            categories=categories, 
            brands=brands, 
            userIsLoggedIn=userIsLoggedIn, 
            user_id=user.id)
    else:
        return render_template('index.html', 
            curCategory=curCategory, 
            categories=categories, 
            brands=brands, 
            userIsLoggedIn=userIsLoggedIn, 
            user_id='')

# clicking on specific brands opens a page with a detailed description
@app.route('/index/<int:category_id>/<int:brand_id>/')
def showDetail(category_id, brand_id):
    brands = session.query(EquipBrand).filter_by(category_id=category_id).all()
    categories = session.query(EquipCategory).all()
    curCategory = session.query(EquipCategory).filter_by(id=category_id).first()
    curBrand = session.query(EquipBrand).filter_by(id=brand_id).first()
    userIsLoggedIn = False
    if 'username' in login_session:
        userIsLoggedIn = True
        user = session.query(User).filter_by(name=login_session['username']).one()
        return render_template('index.html', 
            curCategory=curCategory, 
            categories=categories, 
            brands=brands, 
            curBrand=curBrand, 
            userIsLoggedIn=userIsLoggedIn, 
            user_id=user.id)
    else:
        return render_template('index.html', 
            curCategory=curCategory, 
            categories=categories, 
            brands=brands, 
            curBrand=curBrand, 
            userIsLoggedIn=userIsLoggedIn, 
            user_id='')

# print simply json of category and brand relationships
@app.route('/catalog.json')
def jsonifyCatalog():
    catalogDict = {}
    categories = session.query(EquipCategory).all()
    for i in categories:
        brands = session.query(EquipBrand).filter_by(category_id=i.id).all()
        brandDict = {}
        for j in brands:
            currBrandDict = {}
            currBrandDict['Description'] = j.description
            brandDict[j.name] = currBrandDict
        catalogDict[i.name] = brandDict
    return jsonify(catalogDict)

# set up index page.
# checks to see if db exists, and if so, whether empty.
# if empty, db is initialized by calling 'database_initdata.py'

@app.route('/')
@app.route('/index')
def pvEquipment():
    categories = session.query(EquipCategory).all()
    userIsLoggedIn = False
    if 'username' in login_session:
        userIsLoggedIn = True
        user = session.query(User).filter_by(name=login_session['username']).one()
        return render_template('index.html', 
            categories=categories, 
            userIsLoggedIn=userIsLoggedIn, 
            user_id=user.id)
    else:
        return render_template('index.html', 
            categories=categories, 
            userIsLoggedIn=userIsLoggedIn, 
            user_id='')

if not(os.path.exists(databaseName)):
    database_initdata.py
    print('db initialized')
else:
    print('db exists')
    firstEntry = session.query(EquipCategory).first()
    if not(firstEntry):
        print('db is empty')
        import database_initdata
    else:
        print('db has data')



# for local execution, set debug mode and local port
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
