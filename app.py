from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    starting_bid = db.Column(db.Float, nullable=False)
    current_bid = db.Column(db.Float, default=0.0)
    end_time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def home():
    auctions = Auction.query.all()
    return render_template('home.html', auctions=auctions)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('home'))
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('home'))

@app.route('/create-auction', methods=['GET', 'POST'])
def create_auction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        starting_bid = float(request.form['starting_bid'])
        duration = int(request.form['duration'])
        end_time = datetime.now() + timedelta(hours=duration)
        auction = Auction(
            title=title,
            description=description,
            starting_bid=starting_bid,
            current_bid=starting_bid,
            end_time=end_time,
            user_id=session['user_id']
        )
        db.session.add(auction)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_auction.html')

@app.route('/auction/<int:auction_id>', methods=['GET', 'POST'])
def auction(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    bids = Bid.query.filter_by(auction_id=auction_id).all()
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('login'))
        amount = float(request.form['bid_amount'])
        if amount > auction.current_bid:
            bid = Bid(amount=amount, auction_id=auction_id, user_id=session['user_id'])
            auction.current_bid = amount
            db.session.add(bid)
            db.session.commit()
            flash('Bid placed!')
        else:
            flash('Bid must be higher than current bid.')
    return render_template('auction.html', auction=auction, bids=bids)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
