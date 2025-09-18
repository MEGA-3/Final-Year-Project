from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
import json
import logging
import os


app = Flask(__name__)
app.secret_key = '123'
UPLOAD_FOLDER = 'static/uploads' 

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE'] = 'data.db'

database = 'data.db'

def init_db():
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        mail TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        profile_pic TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS doctor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        mail TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        profile_pic TEXT,
                        specialization TEXT NOT NULL,
                        medical_register_id TEXT NOT NULL UNIQUE)''')
##    cursor.execute("DROP TABLE IF EXISTS user_profile;")

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_profile (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mail TEXT NOT NULL UNIQUE,
                        age INT NOT NULL,
                        speak_verbal TEXT NOT NULL,
                        follow_instruction TEXT NOT NULL,
                        maintain_interaction TEXT NOT NULL,
                        socialize_other_children TEXT NOT NULL,
                        eye_contact TEXT NOT NULL,
                        role_playing TEXT NOT NULL,
                        facial_expression TEXT NOT NULL,
                        understand_others_feelings TEXT NOT NULL,
                        look_at_pointed_toys TEXT NOT NULL,
                        respond_when_called TEXT NOT NULL,
                        keep_attention TEXT NOT NULL,
                        interest_in_gadget TEXT NOT NULL,
                        behaviour TEXT NOT NULL,
                        parent_objective TEXT NOT NULL,
                        gender TEXT NOT NULL,
                        level_ASD_1 TEXT NOT NULL,
                        level_ASD_2 TEXT NOT NULL,
                        status INT NOT NULL
                        )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
                        email TEXT PRIMARY KEY,
                        name TEXT NOT NULL, 
                        profile_data TEXT)''')


    cursor.execute('''CREATE TABLE IF NOT EXISTS suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        prediction TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        suggestion TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_prediction_suggestion (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        profile_data TEXT NOT NULL,
                        prediction TEXT NOT NULL,
                        suggestion TEXT NOT NULL)''')

    
    conn.commit()
    conn.close()

def get_profile_pic(filename):
    if not filename:
        # fallback to first available image or default
        upload_folder = os.path.join(app.root_path, 'static/uploads')
        available_pics = [f for f in os.listdir(upload_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        fallback = available_pics[0] if available_pics else 'default.png'
        return url_for('static', filename='uploads/' + fallback)
    return url_for('static', filename='uploads/' + filename)

def get_user(email):
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE mail = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

with open('stacked_model.pkl', 'rb') as f:
    stacked_model = pickle.load(f)

    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/doctor_details')
def doctor_details():
    return render_template('doctor_details.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Form Data:", request.form) 
        print("Files:", request.files)     

        username = request.form.get('username')
        mail = request.form.get('mail')
        password = request.form.get('password')
        profile_pic = request.files.get('profile_pic')

        if not username or not mail or not password or not profile_pic:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        # Save profile picture
        if profile_pic and profile_pic.filename:
            filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(profile_pic_path)
            profile_pic_url = filename  # 🔥 Store only the filename
        else:
            profile_pic_url = None  

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, mail, password, profile_pic) VALUES (?, ?, ?, ?)",
                           (username, mail, password, profile_pic_url))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or Email already exists. Try a different one.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global username
    if request.method == 'POST':
        username = request.form['mail']
        password = request.form['password']

        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE mail = ? AND password = ?", (username, password,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('dashboard', email=username))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/doctor_register', methods=['GET', 'POST'])
def doctor_register():
    if request.method == 'POST':
        username = request.form['username']
        mail = request.form['mail']
        password = request.form['password']
        specialization = request.form['specialization']
        medical_register_id = request.form['medical_register_id']
        profile_pic = request.files['profile_pic']


        if profile_pic and profile_pic.filename:
            filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(profile_pic_path)
            profile_pic_url = url_for('static', filename='uploads/' + filename)
        else:
            profile_pic_url = None  

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO doctor (username, mail, password, profile_pic, specialization, medical_register_id) VALUES (?, ?, ?, ?, ?, ?)",
                           (username, mail, password, profile_pic_url, specialization, medical_register_id))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('doctor_login'))
        except sqlite3.IntegrityError:
            flash('Username, Email, or Medical Register ID already exists. Try a different one.', 'danger')
        finally:
            conn.close()

    return render_template('doctor_register.html')


@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM doctor WHERE username = ?", (username,))
            result = cursor.fetchone()

        
        if result and result[0] == password:
            session['username'] = username 
            return redirect(url_for('doctor_dashboard'))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template('doctor_login.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():
    username = session.get('username') or request.args.get('username')

    if not username:
        flash("Username not found, please log in again.", "danger")
        return redirect(url_for("doctor_login"))

    session['username'] = username 

    # Fetch profile pic, specialization, and medical_register_id from the database
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT profile_pic, specialization, medical_register_id
            FROM doctor 
            WHERE username = ?
        """, (username,))
        result = cursor.fetchone()

    if result:
        profile_pic, specialization, medical_register_id = result

        # Store values in session
        session['profile_pic'] = profile_pic or None
        session['specialization'] = specialization
        session['medical_register_id'] = medical_register_id  # Store medical_register_id

    # If there's no profile picture in the session, use default or first available pic
    if not session.get('profile_pic'):
        upload_folder = os.path.join(app.root_path, 'static/uploads')
        available_pics = [f for f in os.listdir(upload_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if available_pics:
            session['profile_pic'] = url_for('static', filename='uploads/' + available_pics[0])
        else:
            session['profile_pic'] = None

    # Render the doctor dashboard template with the medical_register_id
    return render_template(
        'doctor_dashboard.html',
        username=session['username'],
        profile_pic=session['profile_pic'],
        specialization=session.get('specialization'),
        medical_register_id=session.get('medical_register_id'),  # Pass medical_register_id to the template
    )


@app.route('/dashboard')
def dashboard():
    email = request.args.get('email')
    user = get_user(email)  # Returns a dict

    if user is None:
        flash("User not found. Please log in again.", "danger")
        return redirect(url_for("login"))

    profile_pic = user.get('profile_pic')
    username = user.get('username')

    if not profile_pic:
        # fallback to any image or default
        upload_folder = os.path.join(app.root_path, 'static/uploads')
        available_pics = [f for f in os.listdir(upload_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if available_pics:
            profile_pic = url_for('static', filename='uploads/' + available_pics[0])
        else:
            profile_pic = url_for('static', filename='uploads/default.png')
    else:
        profile_pic = url_for('static', filename='uploads/' + profile_pic)  # ✅ Only prepend here

    user_dict = {
        'username': username,
        'mail': email,
        'profile_pic': profile_pic
    }

    return render_template(
        'dashboard.html',
        email=email,
        username=username,
        user=user_dict
    )


def get_username_from_email(email):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE mail = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    global username

    if request.method == 'POST':
        # Extract form data
        name = request.form.get('name')
        age = request.form.get('age')
        speak_verbal = request.form.get('speak')
        follow_instruction = request.form.get('follow')
        maintain_interaction = request.form.get('interaction')
        socialize_other_children = request.form.get('socialize_other_children')
        eye_contact = request.form.get('eye_contact')
        role_playing = request.form.get('role_playing')
        facial_expression = request.form.get('facial_express')
        understand_others_feelings = request.form.get('other_feel')
        look_at_pointed_toys = request.form.get('look_at_points')
        respond_when_called = request.form.get('respond')
        keep_attention = request.form.get('keep_attention')
        interest_in_gadget = request.form.get('gadgets')
        behaviour = request.form.get('behavior')
        parent_objective = request.form.get('parent_object')
        gender = request.form.get('gender')
        level_asd_1 = request.form.get('level_1')
        level_asd_2 = request.form.get('level_2')
        print(level_asd_2,"level")
##        level_asd_3 = request.form.get('level_3')

        # Validate required fields
        if not name or not age or not gender:
            flash('Name, Age, and Gender are required fields.', 'danger')
            return redirect(url_for('profile'))
        # Database operations
        with sqlite3.connect(database, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profile WHERE mail = ?", (username,))
            existing_profile = cursor.fetchone()
            print(existing_profile,"profile")

            if existing_profile:
                cursor.execute("""
                    UPDATE user_profile 
                    SET age=?, speak_verbal=?, follow_instruction=?, maintain_interaction=?, 
                        socialize_other_children=?, eye_contact=?, role_playing=?, 
                        faical_expression=?, understand_others_feelings=?, 
                        look_at_poined_toys=?, respond_when_called=?, keep_attention=?, 
                        interest_in_gadget=?, behaviour=?, parent_objective=?, 
                        gender=?, level_ASD_1=?, level_ASD_2=?, status=?
                    WHERE mail=?
                """, (age, speak_verbal, follow_instruction, maintain_interaction, 
                      socialize_other_children, eye_contact, role_playing, 
                      facial_expression, understand_others_feelings, 
                      look_at_pointed_toys, respond_when_called, keep_attention, 
                      interest_in_gadget, behaviour, parent_objective, 
                      gender, level_asd_1, level_asd_2, 0, username))
                flash('Profile updated successfully.', 'info')
            else:
                cursor.execute("""
                    INSERT INTO user_profile (mail, age, speak_verbal, follow_instruction, 
                                              maintain_interaction, socialize_other_children, 
                                              eye_contact, role_playing, facial_expression, 
                                              understand_others_feelings, look_at_pointed_toys, 
                                              respond_when_called, keep_attention, 
                                              interest_in_gadget, behaviour, parent_objective, 
                                              gender, level_ASD_1, level_ASD_2, status) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, age, speak_verbal, follow_instruction, 
                      maintain_interaction, socialize_other_children, eye_contact, 
                      role_playing, facial_expression, understand_others_feelings, 
                      look_at_pointed_toys, respond_when_called, keep_attention, 
                      interest_in_gadget, behaviour, parent_objective, 
                      gender, level_asd_1, level_asd_2, 0))
                flash('Profile created successfully.', 'success')


            # Save profile data in user_profiles table
            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles (email, name, profile_data) 
                VALUES (?, ?, ?)""", (username, name, json.dumps({
                    "age": age,
                    "speak_verbal": speak_verbal,
                    "follow_instruction": follow_instruction,
                    "maintain_interaction": maintain_interaction,
                    "socialize_other_children": socialize_other_children,
                    "eye_contact": eye_contact,
                    "role_playing": role_playing,
                    "facial_expression": facial_expression,
                    "understand_others_feelings": understand_others_feelings,
                    "look_at_pointed_toys": look_at_pointed_toys,
                    "respond_when_called": respond_when_called,
                    "keep_attention": keep_attention,
                    "interest_in_gadget": interest_in_gadget,
                    "behaviour": behaviour,
                    "parent_objective": parent_objective,
                    "gender": gender,
                    "level_asd_1": level_asd_1,
                    "level_asd_2": level_asd_2,
##                    "level_asd_3": level_asd_3,
                })))

            conn.commit()

        return redirect(url_for('profile'))

    return render_template('profile.html')

@app.route('/user_profiles')
def user_profiles():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile")
    users = cursor.fetchall()
    conn.close()
    return render_template('user_profiles.html', users=users)


import logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/predict', methods=['POST'])
def predict():
    logging.info("Form data received: %s", request.form)
    
    # Ensure the expected form field names match those used in the HTML form
    expected_features = [f'field{i}' for i in range(18)]  # Adjusted for 'field0', 'field1', ... 'field17'

    user_data_dict = {}
    user_data_values = []
    errors = []

    # Validate inputs
    for feature in expected_features:
        value = request.form.get(feature)
        user_data_dict[feature] = value

        if not value or value.strip() == "":
            error_msg = f"Missing value for {feature}."
            errors.append(error_msg)
            logging.error(error_msg)
        else:
            try:
                user_data_values.append(float(value))
            except ValueError:
                error_msg = f"Invalid input for {feature}. Please enter a valid number."
                errors.append(error_msg)
                logging.error(error_msg)

    # If errors exist, flash them and redirect **only after validation**
    if errors:
        for error in errors:
            flash(error, "danger")
        logging.info("Redirecting to profile due to validation errors.")
        return redirect(url_for('profile'))  # Redirect **only once**

    # Proceed to prediction if no errors
    user_email = request.form.get('email')
    user_id = request.form.get('user_id')

    features = np.array(user_data_values).reshape(1, -1)
    
    try:
        prediction = stacked_model.predict(features)[0]
        logging.info("Prediction successful. Predicted class index: %s", prediction)
    except Exception as e:
        logging.error("Error during prediction: %s", str(e))
        flash("An error occurred while generating the prediction.", "danger")
        return redirect(url_for('profile'))  

    class_names = ['All', 'Attention', 'Behaviour', 'Not Specified', 
                   'Occupational', 'Sensory Integration', 'Social', 
                   'Social Anxiety', 'Speech']

    predicted_class = class_names[int(prediction)]
    logging.info("Final predicted class: %s", predicted_class)

    # Store prediction in database
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_prediction_suggestion (email, profile_data, prediction, suggestion) VALUES (?, ?, ?, ?)",
                       (user_email, json.dumps(user_data_dict), predicted_class, ""))
        conn.commit()
        conn.close()
        logging.info("Prediction stored in database successfully.")
    except Exception as e:
        logging.error("Error inserting into database: %s", str(e))

    # Render the correct results page
    return render_template('prediction_result.html', 
                           prediction=predicted_class, 
                           user_data=user_data_values, 
                           email=user_email)

@app.route('/submit_suggestion', methods=['POST'])
def submit_suggestion():
    suggestion = request.form.get('suggestion')
    prediction = request.form.get('prediction')
    email = request.form.get('email')

    print(f"Suggestion: {suggestion}, Prediction: {prediction}, Email: {email}")  # Debugging output

    if suggestion and email and prediction and suggestion.strip():
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            # Insert new suggestion
            cursor.execute("INSERT INTO suggestions (email, prediction, suggestion) VALUES (?, ?, ?)",
                           (email, prediction, suggestion))

            conn.commit()  # Commit the transaction
            print("Suggestion stored successfully.")  # Confirmation message
        except Exception as e:
            print(f"Error occurred: {e}")  # Log the error
        finally:
            conn.close()  # Ensure the connection is closed
    else:
        print("Suggestion was empty or invalid.")

    return redirect(f"/my_suggestions?email={email}")

@app.route('/my_suggestions')
def my_suggestions():
    email = request.args.get('email')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Fetch suggestions for the given email
    cursor.execute("SELECT prediction, suggestion FROM suggestions WHERE email = ?", (email,))
    suggestions = cursor.fetchall()

    conn.close()

    print(suggestions)  # Log the fetched suggestions for debugging

    return render_template('my_suggestions.html', suggestions=suggestions)

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('data.db')  # Make sure the path is correct
    conn.row_factory = sqlite3.Row  # Allows for row-based dictionary access
    return conn

@app.route('/user_history', methods=['GET'])
def user_history():
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT suggestions.email, 
                   user_profiles.profile_data, 
                   suggestions.prediction, 
                   suggestions.suggestion
            FROM suggestions
            LEFT JOIN user_profiles 
                ON LOWER(suggestions.email) = LOWER(user_profiles.email)
        """)

        records = cursor.fetchall()

        if not records:
            flash("No prediction or suggestion history found.", "warning")

        return render_template('user_history.html', records=records)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        flash("An error occurred while fetching data.", "danger")
        return redirect(url_for('doctor_dashboard'))

    finally:
        conn.close()

@app.route('/view_history', methods=['GET'])
def view_history():
    patient_email = request.args.get('email')  # ✅ Get the patient's email from URL

    if not patient_email:
        flash("No patient selected.", "danger")
        return redirect(url_for('doctor_dashboard'))

    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_profiles.profile_data, 
                   suggestions.prediction, 
                   suggestions.suggestion 
            FROM suggestions 
            LEFT JOIN user_profiles 
                ON LOWER(suggestions.email) = LOWER(user_profiles.email) 
            WHERE LOWER(suggestions.email) = LOWER(?)
        """, (patient_email,))

        records = cursor.fetchall()

        if not records:
            flash("No history found for this patient.", "warning")

        return render_template('patient_history.html', records=records, name=patient_email)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        flash("An error occurred while fetching data.", "danger")
        return redirect(url_for('doctor_dashboard'))

    finally:
        conn.close()





@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

import webbrowser

if __name__ == '__main__':
    init_db()
    webbrowser.open('http://127.0.0.1:1050')
    app.run(debug=False,port=1050)
