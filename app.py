import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def dashboard():
    search_query = request.args.get('search', '')
    db = get_db()
    
    if search_query:
        vehicles = db.execute(
            "SELECT * FROM vehicles WHERE registration_number LIKE ? OR make LIKE ?", 
            (f'%{search_query}%', f'%{search_query}%')
        ).fetchall()
    else:
        vehicles = db.execute("SELECT * FROM vehicles").fetchall()
        
    return render_template('dashboard.html', vehicles=vehicles, search_query=search_query)

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    db = get_db()
    db.execute(
        """INSERT INTO vehicles (
            vehicle_type, registration_number, make, year, last_roadworthy_date,
            vin_chassis_no, gcm_rating, atm_rating, pbs_permit_no,
            pbs_expiry_date, date_added, date_removed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            request.form.get('vehicle_type'),
            request.form.get('registration_number'),
            request.form.get('make'),
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
    init_db()
    app.run(debug=True) 