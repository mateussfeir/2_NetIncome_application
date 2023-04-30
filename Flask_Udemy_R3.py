
from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import requests
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

''' Joaca's message to Cypher. YOU ARE 2 DAYS STUCK IN HOW TO PLOT YOUR CHART IN A WEBPAGE...
My advice for you tomorrow:
1) Create a new route called simple_chart
2) Create a code that creates a simple chart like with date and some random numbers.
3) Use chat GPT to help you to plot this chart in your web page
4) Once it worked study the process and how it works and rethink about your code.
That is my segestion... hopefully it is gonna work, I am you and you are me so lets keep improving
'''

app = Flask(__name__)
app.secret_key = 'hello'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy allows devs to define database models using Python classes, rather than writing raw SQL.
# It's just like a shortcut

app.permanent_session_lifetime = timedelta(minutes=5)

# Using permanent_session_lifetime we are setting how long the page will log automatically
#  in the last account logged.


# Routes available:
# / Welcome page      
# /login - Allows the user to input his name and e-mail to create his account
# /user - If not logged, redirect to the login page. If logged shows the e-mail saved
# /logout - Logout
# /view - Shows all of the names and e-mails saved on the database
# /new - Route test
# /return_simulator - Asks the user to input the company and shows the real time price


db = SQLAlchemy(app)

# Creating a class to work with database, because in this part we are creating the infra-structure to make possible the creating of accounts\
# in our application

class users(db.Model):
    _id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, name, email):
        self.name = name
        self.email = email


# In this first route '/' we are exporting the information from the base to inheritage the nav bar mainly. and then just using
# basic HTML to print a welcome message to the user.


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/testo')
def testo():
    x = [1, 2, 3, 4]
    y = [275, 225, 250, 250]
    fig = go.Figure(data=go.Scatter(x=x, y=y))
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        font=dict(color="white")
    )
    div = fig.to_html(full_html=False)
    return render_template("testo.html", div_placeholder=div)
 

# In the '/view' route the informations saved in the 'value' list are being displayed.

@app.route('/view')
def view():
    return render_template('view.html', values = users.query.all())



# '/login' route the user can provide the string 'name' that will be saved in the 'nm' variable and his 'email' also.

@app.route('/login', methods = ['POST', 'GET'])
def login(): 
    if request.method == 'POST':
        session.permanent = True
        user = request.form["nm"]
        # we use session (imported from flask library) to store informations
        session['user'] = user

        # users is the class model previous created
        found_user = users.query.filter_by(name=user).first()
        if found_user:
            session['email'] = found_user.email
        else:
            usr = users(user, "")
            db.session.add(usr)
            db.session.commit()
 
        flash('Login Succesful!')
        return redirect(url_for('user'))
    else:
        if 'user' in session:
            flash('Already logged in!')
            return redirect(url_for('user'))
        return render_template('login.html')


@app.route('/user', methods=['POST', 'GET'])
def user():
    # If logged return User: 'Already logged'
    email = None
    if 'user' in session:
        user = session['user']

        if request.method == 'POST':
            email = request.form['email']
            session['email'] = email
            found_user = users.query.filter_by(name=user).first()
            found_user.email = email
            db.session.commit()
            flash('Email was saved!')
        else:
            if 'email' in session:
                email = session['email']
                flash('User already logged in!')

        return render_template('user.html', email=email)
    # If not logged, redirect to the login page
    else:
        flash('You are not logged in')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    flash(f'You have been logged out!', 'info')
    session.pop('user', None)
    session.pop('email', None)
    return redirect(url_for('login'))

# In the simulator page the user has to input 3 informatios: Stock, amount and date.
# Then the code will calculate the profit or loss if the user had held untill today.

@app.route('/simulator', methods = ['POST', 'GET'])
def simulate():
    if request.method == 'POST':
        flash(f'Welcome to the return simulator page.')
        session.permanent = True
        stock = request.form['stock']
        session['stock'] = stock
        money = request.form['money']
        session['money'] = money
        date = request.form['date']
        session['date'] = date

        # 1) Specify API endpoint and parameters

        url = 'https://www.alphavantage.co/query'
        params = {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'symbol': stock,
        'outputsize': 'full',
        'apikey': 'TE1E1KD330UYLRHQ'
        }

        # 2) Make API request and retrieve data

        response = requests.get(url, params=params)
        data = response.json()

        # 3) Check if the asset was opened for trade at the day, in this case we are going to check if
        # the date is in the provided list


        date = request.form['date']

        # 4) Convert data to Pandas DataFrame

        df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)

        # 5) Get the stock price for a specific date

        old_price = df.loc[date]['5. adjusted close']
        session['old_price'] = round(old_price, 2)
        new_price = df.iloc[0]['4. close']
        session['new_price'] = round(new_price, 2)
        percentage_return = round((new_price/old_price - 1)*100, 2)
        session['percentage_return'] = percentage_return
        fmoney = float(money)
        actual_value = (fmoney + (fmoney*(percentage_return/100)))
        session['actual_value'] = actual_value
        profit_loss = actual_value - fmoney
        session['profit_loss'] = profit_loss

        return render_template('simulator_result.html', stock = session['stock'], money = session['money'], date = session['date'], old_price = session.get('old_price'), new_price = session.get('new_price'), percentage_return = session.get('percentage_return'), actual_value = session.get('actual_value'), profit_loss = session.get('profit_loss'))
    else: 
        return render_template('simulator.html')


@app.route('/price', methods = ['POST', 'GET'])
def price():
    if request.method == 'POST':
        session.permanent = True
        stock = request.form['stock']
        session['stock'] = stock
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': stock,
            'outputsize': 'full',
            'apikey': 'TE1E1KD330UYLRHQ'
        }
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        price = df.iloc[0]['4. close']
        session['price'] = price
        if 'stock' in session:
            return render_template('price.html', stock=session['stock'], data=session.get('price', ""))
        else:
            return redirect(url_for('index'))
    return render_template('price.html')


@app.route('/chart', methods=['GET', 'POST'])
def chart():
    stock = session.get('stock', 'AAPL')

    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'INCOME_STATEMENT',
        'symbol': stock,
        'apikey': 'TE1E1KD330UYLRHQ'
    }

    response = requests.get(url, params=params)
    data = response.json()
    earnings_list = []

    for earnings in data['quarterlyReports']:
        financial_data = float(earnings['netIncome'])
        fiscal_date = earnings['fiscalDateEnding']
        earnings_list.append((fiscal_date, financial_data))

    earnings_list.reverse()
    dates = [inf[0] for inf in earnings_list]
    financial_data = [inf[1] for inf in earnings_list]
    chosen_data_billion = [x / 1000000000 for x in financial_data]

    # Create a bar chart using plotly.graph_objs
    trace = go.Bar(x=dates, y=chosen_data_billion)
    layout = go.Layout(
        title=f"{stock}'s {'quarterly'} {'Net Income'}",
        xaxis=dict(title='Date'),
        yaxis=dict(title='Earnings (Billion)'),
        paper_bgcolor='black',
        plot_bgcolor='black',
        font=dict(color='white')
    )
    fig = go.Figure(data=[trace], layout=layout)

    # Save the chart to an HTML file
    chart_html = plot(fig, output_type='div', include_plotlyjs=True)

    if request.method == 'POST':
        session.permanent = True
        stock = request.form['stock']
        session['stock'] = stock
        return render_template('chart_redirectory.html', stock = stock, chart_html=chart_html)

    return render_template('chart.html', chart_html=chart_html)


@app.route('/simulator_result')
def test():
    return render_template('simulator_result.html', stock = session['stock'], money = session['money'], date = session['date'], old_price = session.get('old_price'), new_price = session.get('new_price'), percentage_return = session.get('percentage_return'), actual_value = session.get('actual_value'), profit_loss = session.get('profit_loss'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port= 8080)


''' 
Flask course from Udemy.

 There are 5 most important HTTP words:
 POST : Add data ('Secured information')
 GET : Retrieve Data ('Not secure, you do not care if someone sees it')
 DELETE : Remove Data
 PATCH : Update Data
 PUT : Replace Data

Data Formats: HTML and JSON

Goal of this code:
Make a webpage where the user can choose the company and receive the data related to its financial statement
(Specially the revenue and profit) or parhaps just even the price of a chosen stock.
The main purpose is to learn how to creat an UI where the user can input some information and receive a feedback
'''