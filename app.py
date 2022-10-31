import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, get_flashed_messages
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from datetime import date
from datetime import timedelta


import requests
import urllib.parse
import json

from helpers import apology, login_required, lookup, usd
from collections import OrderedDict


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    index_data = []
    index_data_graph = []
    total=0
    profit=0
    invested=0
    names=[]

    data = db.execute("select * from purchases where user_id = " + str(session["user_id"]))
    data2 = db.execute("select * from users where id = " + str(session["user_id"]))
    data3 = db.execute("select * from stock_history")
    delete = db.execute("select * from purchases where shares = 0 and user_id = " + str(session["user_id"]))


    


    
    for x in delete:
        db.execute("delete from purchases where user_id = " + str(session["user_id"]) + " and shares = 0")




    if len(data) <1:
        index_data.append({
            'symbol': None,
            'name': None,
            'shares': None,
            'price_now': None,
            'price_then': None,
            'total_line': None,
            'total': 10000,
            'price_per_one': None
        })
    
    stock={
        "nflx": [],
        "googl": [],
        "tsla": [],
        "fb": [],
        "amzn": [],
        "date": []    
    }


    for x in range(len(data)):
        y = lookup(data[x]['symbol'])
        w = y['name']
        z = y['price']
        

        index_data.append({
            'symbol': data[x]['symbol'],
            'name': w,
            'shares': data[x]['shares'],
            'price_now': round(z*data[x]['shares'], 3),
            'price_then': round(data[x]['price_per_shares']*data[x]['shares'], 3),
            'total_line': round(data[x]['shares']*data[x]['price_per_shares'], 3),
            'total': round(data2[0]['cash'], 3),
            'price_per_one': z,
            'p': 0
            })
        names.append(w)

        

        invested+=round(data[x]['price_per_shares']*data[x]['shares'], 3)
        profit+=round(round(z*data[x]['shares'], 3) - round(data[x]['price_per_shares']*data[x]['shares'], 3), 3)
        total+=round(z*data[x]['shares'], 3)

    for x in range(len(index_data)):
        try:
            index_data[x]['p'] = round(((round(index_data[x]['price_now']-index_data[x]['price_then'],2))/index_data[x]['price_then'])*100,2)
        except:
            pass
    stock_history = []

    for x in data3:

        if x['company'] == "nflx": 
            stock['nflx'].append(x['stock'])
            stock['date'].append(x['date']) 
        if x['company'] == "googl": stock['googl'].append(x['stock']) 
        if x['company'] == "tsla": stock['tsla'].append(x['stock'])
        if x['company'] == "FB": stock['fb'].append(x['stock'])
        if x['company'] == "AMZN": stock['amzn'].append(x['stock'])
    

    dat = date.today()
    dat = dat - timedelta(days = 1)
    print(dat)

    doesExist = db.execute("select value from graph where date = '" +  str(dat)+"' and user_id = " + str(session["user_id"]))
    print(doesExist)
    if doesExist == []:
        db.execute("insert into graph (user_id, date, value) values (?,?,?)", str(session["user_id"]),  str(dat), str(index_data[0]['total'] + invested + profit) )

    graph = db.execute("select * from graph where user_id = " + str(session["user_id"]))

    dates = []
    values = []
    for i in graph:
        dates.append(i['Date'])
        values.append(i['value'])


    print(index_data)
    return render_template("index.html", data=index_data, total=round(total,3), profit=round(profit, 3), invested=round(invested,3) ,names=names, graph=stock, dates=dates, values=values)


@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    
    if request.method == "POST":
        timeline = request.form.get('Timeline')
        if timeline == '30':
            timeline = 23
    else:
        timeline = 6


    symbol = request.args.to_dict().get('data')
    #timeline = request.form['date']
    print("timeline -> " + str(timeline))




    try:
        #api_key = os.environ.get("API_KEY")
        #api_key = "pk_6c70509ce93d4b36b2d416f60ca29a06"
        api_key = "pk_6bc02c1e81814732a6f5a5d63b96932d"

        #url = "https://cloud.iexapis.com/stable/stock/" + str(symbol) +"/quote?token=" + str(api_key)
        baseUrl = "https://cloud.iexapis.com/stable/"
        param = "?token=" + str(api_key)


        url = "https://cloud.iexapis.com/time-series/REPORTED_FINANCIALS/AAPL/10-Q?range=1y?token=" + str(api_key)
        response = requests.get(baseUrl+'stock/'+ str(symbol) +'/chart'+param)
        response.raise_for_status()
    except requests.RequestException:
        print("[error] -> requests.RequestException")

    
    quote = response.json()
    
    
    data = []
    final = []

    dates = []
    values = []
    i=-1

    print(-(int(timeline)))

    while i > -(int(timeline)):
        data.append({
            'closeP': quote[i]['close'],
            'openP': quote[i]['open'],
            'date': quote[i]['priceDate'],
            'changeP': round(quote[i]['close'] - quote[i]['open'], 3)
        })
        dates.append(quote[i]['priceDate'])
        values.append(quote[i]['close'])
        i=i-1
        print(i)
        
        
    
    dates.reverse()
    values.reverse()
     


    return render_template("predict.html", data=data, dates=dates, values=values, name=symbol, timeline=timeline)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    current_cash= db.execute("select cash from users where id = " + str(session["user_id"]))[0]['cash']

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        already_done = db.execute("select * from purchases where user_id ="+ str(session['user_id']) +" and symbol = '"+ str(symbol) +"'")

        if already_done != []:
            return apology("You can only have one purchase per stock", 400)
        

        x=lookup(symbol)


        if x == None:
            return apology("invalid symbol", 400)

        if current_cash < x['price']*int(shares):
            return apology("You don't have enough money", 400)
 

        price = int(shares)*x['price']
        new_cash = current_cash - price


        db.execute("UPDATE users SET cash = "+ str(new_cash) +" WHERE id = "+ str(session["user_id"]) +";")
        db.execute("insert into purchases (user_id, shares, symbol, price_total, price_per_shares) values (?, ?, ?, ?,? )", session["user_id"], shares, symbol, price, x['price'])
        db.execute("insert into history (user_id, type, amount, time, shares, name) values (?,?,?,?,?,?)",str(session["user_id"]), "buy", str(price), str(datetime.now()), str(shares), symbol)
        return redirect("/")

    return render_template("buy.html")

'''
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    data = db.execute("select * from history where user_id = " + str(session["user_id"]))
    return render_template("history.html", data=data)
'''

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    get_flashed_messages()

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        #[!] delete the comment when finised
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Your password or username is wrong", 'error')
            return redirect("/")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        data = lookup(request.form.get("symbol"))
        if data == None:
            return apology("invalid symbol",400)
        return render_template("quote.html", value=True, data=data)
        return redirect("/")
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    data = db.execute("select username from users")




    if request.method == "POST":


        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        passwordHash = generate_password_hash(password)

        if username == "" or password == "" or confirm == "":
            return apology("no input values")

        if password != confirm:
            return apology("your password and confirm are not the same")

        for x in data:
            if x['username'] == username:
                return apology("this username is already used")

        db.execute("insert into users (username, hash) values (?, ?)", username, passwordHash)

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    data = db.execute("select * from purchases where user_id = " + str(session["user_id"]))
    data2 = db.execute("select * from users where id = " + str(session["user_id"]))
    delete = db.execute("select * from purchases where shares = 0 and user_id = " + str(session["user_id"]))
    z = db.execute("select shares, symbol from purchases where user_id = " + str(session["user_id"]))
    


    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        for x in z:
            if x["symbol"] == symbol:
                if int(x["shares"]) < int(shares):
                    return apology("You don't have this many shares")

        x = db.execute("select * from purchases where user_id = " + str(session["user_id"]))
        

        y=next(item for item in x if item['symbol'] == symbol)
        
        price_per_stock = lookup(symbol)['price']
        price_before_sell = price_per_stock * int(shares)
        price_finale = data2[0]['cash'] + price_before_sell
        db.execute("UPDATE users SET cash = "+ str(price_finale) +" WHERE id = "+ str(session["user_id"]) +";")
        
        if y['shares'] == 1 or y['shares'] == shares:
            db.execute("DELETE FROM purchases WHERE user_id = " + str(session["user_id"]) + " and shares = "+ str(shares) + " and symbol = '" + symbol+"'")
        else:
            db.execute("UPDATE purchases SET shares="+ str(int(y['shares'])-int(shares)) +" WHERE user_id ="+ str(session['user_id'])+" and symbol = '"+symbol+"'")
        db.execute("insert into history (user_id, type, amount, time, shares, name) values (?,?,?,?,?,?)",str(session["user_id"]), "sell", str(price_before_sell), str(datetime.now()), str(shares), symbol)
        
        for x in delete:
            db.execute("DELETE FROM purchases WHERE shares = 0 AND user_id = " + str(session["user_id"]))
        flash("If there is still a line of zero's with the stock that you just sold please reload the page to make it disappear")
        return redirect("/")
    return render_template("sell.html", data=data, data2=z)
    


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
