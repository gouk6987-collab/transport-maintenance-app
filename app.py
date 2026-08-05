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
            "SELECT * FROM vehicles WHERE registration_number LIKE ?", 
            (f'%{search_query}%',)
        ).fetchall()
    else:
        vehicles = db.execute("SELECT * FROM vehicles").fetchall()
        
    return render_template('dashboard.html', vehicles=vehicles, search_query=search_query)

# Route to add a new vehicle record
@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    rego = request.form.get('registration_number')
    v_type = request.form.get('vehicle_type')
    make = request.form.get('make')
    model = request.form.get('model')
    year = request.form.get('year')

    if rego and v_type:
        db = get_db()
        db.execute(
            "INSERT INTO vehicles (registration_number, vehicle_type, make, model, year) VALUES (?, ?, ?, ?, ?)",
            (rego, v_type, make, model, year)
        )
        db.commit()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)