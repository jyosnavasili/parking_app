from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'parking.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
    user = cur.fetchone()
    if user:
        return jsonify({"message": "Login successful!", "user_id": user[0]})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/check-in', methods=['POST'])
def check_in():
    data = request.json
    user_id = data['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM ParkingSpots WHERE is_occupied = 0 LIMIT 1")
    spot = cur.fetchone()
    if spot:
        spot_id = spot[0]
        cur.execute("INSERT INTO ParkedCars (user_id, spot_id) VALUES (?, ?)", (user_id, spot_id))
        cur.execute("UPDATE ParkingSpots SET is_occupied = 1 WHERE id = ?", (spot_id,))
        conn.commit()
        return jsonify({"message": "Checked in", "spot_id": spot_id}), 200
    else:
        return jsonify({"message": "No available spots"}), 400

@app.route('/check-out', methods=['POST'])
def check_out():
    data = request.json
    user_id = data['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT spot_id FROM ParkedCars WHERE user_id = ? ORDER BY check_in_time DESC LIMIT 1", (user_id,))
    spot = cur.fetchone()
    if spot:
        spot_id = spot[0]
        cur.execute("UPDATE ParkingSpots SET is_occupied = 0 WHERE id = ?", (spot_id,))
        cur.execute("DELETE FROM ParkedCars WHERE user_id = ? AND spot_id = ?", (user_id, spot_id))
        conn.commit()
        return jsonify({"message": "Checked out", "spot_id": spot_id}), 200
    else:
        return jsonify({"message": "No car found for this user"}), 400

@app.route('/spot/<int:user_id>', methods=['GET'])
def get_spot(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT spot_id FROM ParkedCars WHERE user_id = ? ORDER BY check_in_time DESC LIMIT 1", (user_id,))
    spot = cur.fetchone()
    if spot:
        return jsonify({"spot_id": spot[0]}), 200
    else:
        return jsonify({"message": "No car found for this user"}), 400

if __name__ == '__main__':
    app.run(debug=True)
