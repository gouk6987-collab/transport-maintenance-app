DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS vehicles;

-- Table to store user login accounts
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Table to store vehicle register records
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_type TEXT,
    registration_number TEXT NOT NULL,
    make TEXT,
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