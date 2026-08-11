import os
import io
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_later'

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    if not DATABASE_URL:
        return
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    ''')
    
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
    
    cur.execute("SELECT * FROM users WHERE username = %s;", ('DT',))
    user = cur.fetchone()
    if user:
        cur.execute("UPDATE users SET password = %s WHERE username = %s;", ('DuhanTransport1981', 'DT'))
    else:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s);", ('DT', 'DuhanTransport1981'))
        
    conn.commit()
    cur.close()
    conn.close()

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
        cur.execute(
            "SELECT * FROM vehicles WHERE registration_number ILIKE %s OR make ILIKE %s ORDER BY id DESC;", 
            (f'%{search_query}%', f'%{search_query}%')
        )
    else:
        cur.execute("SELECT * FROM vehicles ORDER BY id DESC;")
        
    vehicles = cur.fetchall()
    cur.close()
    conn.close()
        
    return render_template('dashboard.html', vehicles=vehicles, search_query=search_query, user=session.get('username'))

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO vehicles (
            vehicle_type, registration_number, make, model, year, last_roadworthy_date,
            vin_chassis_no, gcm_rating, atm_rating, pbs_permit_no,
            pbs_expiry_date, date_added, date_removed
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
        (
            request.form.get('vehicle_type'),
            request.form.get('registration_number'),
            request.form.get('make'),
            request.form.get('model'),
            request.form.get('year') or None,
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
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete_vehicle/<int:id>', methods=['GET'])
def delete_vehicle(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM vehicles WHERE id = %s;", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/export')
def export_vehicles():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM vehicles ORDER BY registration_number ASC;")
    vehicles = cur.fetchall()
    cur.close()
    conn.close()

    # Build PDF using ReportLab
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(letter),
        rightMargin=20, 
        leftMargin=20, 
        topMargin=20, 
        bottomMargin=20
    )
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#111111'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#28a745'),
        spaceAfter=15
    )

    elements.append(Paragraph("<b>DUHAN TRANSPORT</b>", title_style))
    elements.append(Paragraph("Official Fleet Vehicle Register", subtitle_style))

    # Table headers
    data = [[
        "Type", "Rego", "Make", "Year", "Roadworthy",
        "VIN / Chassis", "GCM", "ATM", "PBS #", "PBS Expiry", "Date Added"
    ]]

    # Table rows
    for v in vehicles:
        data.append([
            v.get('vehicle_type') or '-',
            v.get('registration_number') or '-',
            v.get('make') or '-',
            str(v.get('year') or '-'),
            v.get('last_roadworthy_date') or '-',
            v.get('vin_chassis_no') or '-',
            v.get('gcm_rating') or '-',
            v.get('atm_rating') or '-',
            v.get('pbs_permit_no') or '-',
            v.get('pbs_expiry_date') or '-',
            v.get('date_added') or '-'
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#222222')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=Duhan_Transport_Vehicle_Register.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
