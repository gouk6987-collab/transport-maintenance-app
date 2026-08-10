import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_later'
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        # Create users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create vehicles table
        db.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_type TEXT,
                registration_number TEXT NOT NULL,
                make TEXT,
                model TEXT,
                year INTEGER,
                last_roadworthy_date TEXT,
                vin_chassis_no TEXT,
                gcm_rating TEXT,
                atm_rating TEXT,
                pbs_permit_no TEXT,
                pbs_expiry_date TEXT,
                date_added TEXT,
                date_removed TEXT
            )
        ''')
        # Insert or update the DT account password
        db.execute("""
            INSERT INTO users (username, password) VALUES ('DT', 'DuhanTransport1981')
            ON CONFLICT(username) DO UPDATE SET password = excluded.password
        """)
        db.commit()

# Initialize DB on start
init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            error = 'Please fill out all fields.'
        else:
            try:
                db = get_db()
                existing_user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
                
                if existing_user:
                    error = 'Username already taken. Please choose another.'
                else:
                    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    db.commit()
                    return redirect(url_for('login'))
            except Exception as e:
                error = f"Database error: {str(e)}"
            
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    search_query = request.args.get('search', '')
    db = get_db()
    
    if search_query:
        vehicles = db.execute(
            "SELECT * FROM vehicles WHERE registration_number LIKE ? OR make LIKE ?", 
            (f'%{search_query}%', f'%{search_query}%')
        ).fetchall()
    else:
        vehicles = db.execute("SELECT * FROM vehicles").fetchall()
        
    return render_template('dashboard.html', vehicles=vehicles, search_query=search_query, user=session.get('username'))

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = get_db()
    db.execute(
        """INSERT INTO vehicles (
            vehicle_type, registration_number, make, model, year, last_roadworthy_date,
            vin_chassis_no, gcm_rating, atm_rating, pbs_permit_no,
            pbs_expiry_date, date_added, date_removed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            request.form.get('vehicle_type'),
            request.form.get('registration_number'),
            request.form.get('make'),
            request.form.get('model'),
            request.form.get('year'),
            request.form.get('last_roadworthy_date'),
            request.form.get('vin_chassis_no'),
            request.form.get('gcm_rating'),
            request.form.get('atm_rating'),
            request.form.get('pbs_permit_no'),
            request.form.get('pbs_expiry_date'),
            request.form.get('date_added'),
            request.form.get('date_removed')
        )
    )
    db.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
