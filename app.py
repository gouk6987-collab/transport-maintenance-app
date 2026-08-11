import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from weasyprint import HTML

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_later'

# Fetch PostgreSQL database URL from Render Environment Variables
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    if not DATABASE_URL:
        return
    
    conn = get_db()
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    ''')
    
    # Create vehicles table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id SERIAL PRIMARY KEY,
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
        );
    ''')
    
    # Insert default DT user
    cur.execute("SELECT * FROM users WHERE username = %s;", ('DT',))
    user = cur.fetchone()
    if user:
        cur.execute("UPDATE users SET password = %s WHERE username = %s;", ('DuhanTransport1981', 'DT'))
    else:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s);", ('DT', 'DuhanTransport1981'))
        
    conn.commit()
    cur.close()
    conn.close()

# Initialize DB structure on startup
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
                conn = get_db()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
                existing_user = cur.fetchone()
                
                if existing_user:
                    error = 'Username already taken.'
                else:
                    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s);", (username, password))
                    conn.commit()
                    cur.close()
                    conn.close()
                    return redirect(url_for('login'))
                cur.close()
                conn.close()
            except Exception as e:
                error = f"Database error: {str(e)}"
            
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s;", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
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
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if search_query:
        cur.execute
