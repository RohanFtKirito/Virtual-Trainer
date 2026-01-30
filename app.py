"""
Unified Flask Application for Virtual Trainer
Combines pose detection website and diet recommendation system
Features: User authentication, database storage, REST API endpoints
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import pickle
import pandas as pd
import csv
import os

# ==================== Flask Configuration ====================
app = Flask(__name__, template_folder='.', static_folder='assets')

# Secret key for sessions (change in production)
app.config['SECRET_KEY'] = 'virtual-trainer-secret-key-2024'

# Database configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///virtual_trainer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load diet recommendation model and data
MODEL_PATH = os.path.join(BASE_DIR, 'diet-recommendation-system-main', 'food_model.pickle')
DATA_PATH = os.path.join(BASE_DIR, 'diet-recommendation-system-main', 'done_food_data.csv')

# Load model and data
model = None
food_data = None

try:
    with open(MODEL_PATH, 'rb') as file:
        model = pickle.load(file)
    food_data = pd.read_csv(DATA_PATH)
    print("Diet model and data loaded successfully!")
except Exception as e:
    print(f"Warning: Could not load diet model: {e}")


def read_csv(file_path, sort_by='Descrip'):
    """Read and sort CSV file"""
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        sorted_rows = sorted(rows, key=lambda x: x[sort_by])
        return sorted_rows


# ==================== Database Models ====================

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    exercise_history = db.relationship('ExerciseHistory', backref='user', lazy=True)
    diet_logs = db.relationship('DietLog', backref='user', lazy=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class ExerciseHistory(db.Model):
    """Track user's exercise history"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_name = db.Column(db.String(50), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=True)
    repetitions = db.Column(db.Integer, nullable=True)
    calories_burned = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"ExerciseHistory('{self.exercise_name}', {self.created_at})"


class DietLog(db.Model):
    """Track user's diet logs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    fibre = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"DietLog('{self.food_name}', '{self.category}')"


# ==================== Authentication Routes ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        # Hash password and create user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ==================== Dashboard Route ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with progress tracking"""
    # Get user stats
    total_exercises = ExerciseHistory.query.filter_by(user_id=current_user.id).count()
    total_diet_logs = DietLog.query.filter_by(user_id=current_user.id).count()
    
    # Get recent activities
    recent_exercises = ExerciseHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ExerciseHistory.created_at.desc()).limit(5).all()
    recent_diets = DietLog.query.filter_by(user_id=current_user.id)\
        .order_by(DietLog.created_at.desc()).limit(5).all()
    
    # Calculate total calories burned
    total_calories = db.session.query(db.func.sum(ExerciseHistory.calories_burned))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('dashboard.html', 
                           total_exercises=total_exercises,
                           total_diet_logs=total_diet_logs,
                           total_calories=round(total_calories, 2),
                           recent_exercises=recent_exercises,
                           recent_diets=recent_diets)


# ==================== Main Website Routes ====================

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')


@app.route('/index.html')
def home():
    """Home page"""
    return render_template('index.html')


@app.route('/about.html')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/courses.html')
def courses():
    """Courses page"""
    return render_template('courses.html')


@app.route('/gallery.html')
def gallery():
    """Gallery page"""
    return render_template('gallery.html')


@app.route('/blog.html')
def blog():
    """Blog listing page"""
    return render_template('blog.html')


@app.route('/blog_details.html')
def blog_details():
    """Blog details page"""
    return render_template('blog_details.html')


@app.route('/elements.html')
def elements():
    """Elements page"""
    return render_template('elements.html')


@app.route('/contact.html')
def contact():
    """Contact page"""
    return render_template('contact.html')


@app.route('/pricing.html')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


@app.route('/index2.html')
def training():
    """Training page with pose detection exercises"""
    return render_template('index2.html')


# ==================== Exercise Camera Routes ====================

@app.route('/exercise-bicepcurl.html')
def exercise_bicepcurl():
    """Bicep curl camera page with rep counting"""
    return render_template('exercise-bicepcurl.html')


@app.route('/exercise-plank.html')
def exercise_plank():
    """Plank camera page with timer and form score"""
    return render_template('exercise-plank.html')


@app.route('/exercise-pushup.html')
def exercise_pushup():
    """PushUp camera page with rep counting"""
    return render_template('exercise-pushup.html')


@app.route('/exercise-downwarddog.html')
def exercise_downwarddog():
    """Downward dog camera page with timer"""
    return render_template('exercise-downwarddog.html')


# ==================== Pose Detection Routes ====================

@app.route('/execute/<pose>')
def execute_pose(pose):
    """Execute a pose detection script - opens camera in new terminal"""
    # Map pose names to Python files
    pose_files = {
        'BicepCurl': 'new python/BicepCurl_final.py',
        'Plank': 'new python/Plank.py',
        'PushUp': 'new python/PushUp.py',
        'DownwardFacingDog': 'new python/DownwardFacingDog.py'
    }
    
    if pose not in pose_files:
        return f'Unknown pose: {pose}'
    
    script_path = os.path.join(BASE_DIR, 'new python', pose_files[pose])
    
    try:
        # Open the script in a new terminal window so the camera can be displayed
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)
        
        # Use AppleScript to open Terminal and run the exercise script
        cmd = f'osascript -e \'tell application "Terminal" to do script "cd \\"{script_dir}\\" && python3 \\"{script_name}\\"; exit"\''
        os.system(cmd)
        
        return 'Camera started! A terminal window should have opened with the camera feed. Press Q to quit.'
    except Exception as e:
        return f'Error: {str(e)}'


# ==================== Diet Recommendation Routes ====================

@app.route('/diet')
def diet_home():
    """Diet recommendation system home"""
    return render_template('diet-mainpage.html')


@app.route('/diet', methods=['POST'])
def diet_predict():
    """Predict diet category based on macros"""
    if model is None:
        return render_template('diet-mainpage.html', result='Error: Model not loaded')
    
    try:
        input_1 = float(request.form['input_1'])  # Calories
        input_2 = float(request.form['input_2'])  # Protein
        input_3 = float(request.form['input_3'])  # Fibre
        
        inputs = [[input_1, input_2, input_3]]
        prediction = model.predict(inputs)
        
        if prediction[0] == 'Muscle_Gain':
            result = 'Muscle Gain'
        elif prediction[0] == 'Weight_Gain':
            result = 'Weight Gain'
        elif prediction[0] == 'Weight_Loss':
            result = 'Weight Loss'
        else:
            result = 'General food'
        
        return render_template('diet-mainpage.html', result=result)
    except Exception as e:
        return render_template('diet-mainpage.html', result=f'Error: {str(e)}')


@app.route('/diet/musclegain', methods=['POST'])
def musclegain():
    """Filter muscle gain foods"""
    if food_data is None:
        return render_template('diet-mainpage.html', musclegainfoods='Error: Data not loaded')
    
    try:
        vegetarian = request.form.getlist('vegetarian')
        iron = request.form.getlist('iron')
        calcium = request.form.getlist('calcium')
        anyfoods = request.form.getlist('anyfoods')
        
        muscle_gain_data = food_data[food_data['category'] == 'Muscle_Gain']
        
        if 'iron' in iron:
            muscle_gain_data = muscle_gain_data[muscle_gain_data['Iron_mg'] > 6]
        if 'calcium' in calcium:
            muscle_gain_data = muscle_gain_data[muscle_gain_data['Calcium_mg'] > 150]
        if 'vegetarian' in vegetarian:
            exclude_keywords = ['Egg', 'Fish', 'meat', 'beef', 'Chicken', 'Beef', 'Deer', 
                               'lamb', 'crab', 'pork', 'Frog legs', 'Pork', 'Turkey', 
                               'flesh', 'Ostrich', 'Emu', 'cuttelfish', 'Seaweed', 
                               'crayfish', 'shrimp', 'Octopus']
            pattern = '|'.join(exclude_keywords)
            muscle_gain_data = muscle_gain_data[~muscle_gain_data['Descrip'].str.contains(pattern, case=False, na=False)]
        if 'anyfoods' in anyfoods or (not iron and not calcium and not vegetarian):
            muscle_gain_data = food_data[food_data['category'] == 'Muscle_Gain']
        
        if len(muscle_gain_data) > 0:
            musclegainfoods = muscle_gain_data['Descrip'].sample(n=min(5, len(muscle_gain_data))).to_string(index=False)
        else:
            musclegainfoods = 'No foods match your criteria'
        
        return render_template('diet-mainpage.html', musclegainfoods=musclegainfoods)
    except Exception as e:
        return render_template('diet-mainpage.html', musclegainfoods=f'Error: {str(e)}')


@app.route('/diet/weightgain', methods=['POST'])
def weightgain():
    """Filter weight gain foods"""
    if food_data is None:
        return render_template('diet-mainpage.html', weightgainfoods='Error: Data not loaded')
    
    try:
        vegetarian = request.form.getlist('vegetarian')
        iron = request.form.getlist('iron')
        calcium = request.form.getlist('calcium')
        anyfoods = request.form.getlist('anyfoods')
        
        weight_gain_data = food_data[food_data['category'] == 'Weight_Gain']
        
        if 'iron' in iron:
            weight_gain_data = weight_gain_data[weight_gain_data['Iron_mg'] > 6]
        if 'calcium' in calcium:
            weight_gain_data = weight_gain_data[weight_gain_data['Calcium_mg'] > 150]
        if 'vegetarian' in vegetarian:
            exclude_keywords = ['Egg', 'Fish', 'meat', 'beef', 'Chicken', 'Beef', 'Deer', 
                               'lamb', 'crab', 'pork', 'turkey', 'flesh']
            pattern = '|'.join(exclude_keywords)
            weight_gain_data = weight_gain_data[~weight_gain_data['Descrip'].str.contains(pattern, case=False, na=False)]
        if 'anyfoods' in anyfoods or (not iron and not calcium and not vegetarian):
            weight_gain_data = food_data[food_data['category'] == 'Weight_Gain']
        
        if len(weight_gain_data) > 0:
            weightgainfoods = weight_gain_data['Descrip'].sample(n=min(5, len(weight_gain_data))).to_string(index=False)
        else:
            weightgainfoods = 'No foods match your criteria'
        
        return render_template('diet-mainpage.html', weightgainfoods=weightgainfoods)
    except Exception as e:
        return render_template('diet-mainpage.html', weightgainfoods=f'Error: {str(e)}')


@app.route('/diet/weightloss', methods=['POST'])
def weightloss():
    """Filter weight loss foods"""
    if food_data is None:
        return render_template('diet-mainpage.html', weightlossfoods='Error: Data not loaded')
    
    try:
        vegetarian = request.form.getlist('vegetarian')
        iron = request.form.getlist('iron')
        calcium = request.form.getlist('calcium')
        anyfoods = request.form.getlist('anyfoods')
        
        weight_loss_data = food_data[food_data['category'] == 'Weight_Loss']
        
        if 'iron' in iron:
            weight_loss_data = weight_loss_data[weight_loss_data['Iron_mg'] > 6]
        if 'calcium' in calcium:
            weight_loss_data = weight_loss_data[weight_loss_data['Calcium_mg'] > 150]
        if 'vegetarian' in vegetarian:
            exclude_keywords = ['Egg', 'Fish', 'meat', 'beef', 'Chicken', 'Beef', 'Deer', 
                               'lamb', 'crab', 'pork', 'turkey', 'flesh']
            pattern = '|'.join(exclude_keywords)
            weight_loss_data = weight_loss_data[~weight_loss_data['Descrip'].str.contains(pattern, case=False, na=False)]
        if 'anyfoods' in anyfoods or (not iron and not calcium and not vegetarian):
            weight_loss_data = food_data[food_data['category'] == 'Weight_Loss']
        
        if len(weight_loss_data) > 0:
            weightlossfoods = weight_loss_data['Descrip'].sample(n=min(5, len(weight_loss_data))).to_string(index=False)
        else:
            weightlossfoods = 'No foods match your criteria'
        
        return render_template('diet-mainpage.html', weightlossfoods=weightlossfoods)
    except Exception as e:
        return render_template('diet-mainpage.html', weightlossfoods=f'Error: {str(e)}')


@app.route('/diet/search', methods=['POST', 'GET'])
def diet_search():
    """Search all foods"""
    if food_data is None:
        return render_template('diet-search.html', rows=[])
    
    try:
        rows = read_csv(DATA_PATH)
        return render_template('diet-search.html', rows=rows)
    except Exception as e:
        return render_template('diet-search.html', rows=[], error=str(e))


# ==================== REST API Endpoints ====================

# --- Users API ---

@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users (admin only)"""
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'created_at': u.created_at.isoformat()
    } for u in users])


@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def api_get_user(user_id):
    """Get specific user info"""
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    })


# --- Exercises API ---

@app.route('/api/exercises', methods=['GET'])
@login_required
def api_get_exercises():
    """Get user's exercise history"""
    exercises = ExerciseHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ExerciseHistory.created_at.desc()).all()
    return jsonify([{
        'id': e.id,
        'exercise_name': e.exercise_name,
        'duration_seconds': e.duration_seconds,
        'repetitions': e.repetitions,
        'calories_burned': e.calories_burned,
        'created_at': e.created_at.isoformat()
    } for e in exercises])


@app.route('/api/exercises', methods=['POST'])
@login_required
def api_add_exercise():
    """Log a new exercise"""
    data = request.get_json()
    
    exercise = ExerciseHistory(
        user_id=current_user.id,
        exercise_name=data.get('exercise_name'),
        duration_seconds=data.get('duration_seconds'),
        repetitions=data.get('repetitions'),
        calories_burned=data.get('calories_burned')
    )
    db.session.add(exercise)
    db.session.commit()
    
    return jsonify({'message': 'Exercise logged successfully', 'id': exercise.id}), 201


@app.route('/api/exercises/<int:exercise_id>', methods=['DELETE'])
@login_required
def api_delete_exercise(exercise_id):
    """Delete an exercise log"""
    exercise = ExerciseHistory.query.get_or_404(exercise_id)
    if exercise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(exercise)
    db.session.commit()
    return jsonify({'message': 'Exercise deleted successfully'})


# --- Diet API ---

@app.route('/api/diet', methods=['GET'])
@login_required
def api_get_diet():
    """Get user's diet logs"""
    diets = DietLog.query.filter_by(user_id=current_user.id)\
        .order_by(DietLog.created_at.desc()).all()
    return jsonify([{
        'id': d.id,
        'food_name': d.food_name,
        'category': d.category,
        'calories': d.calories,
        'protein': d.protein,
        'fibre': d.fibre,
        'created_at': d.created_at.isoformat()
    } for d in diets])


@app.route('/api/diet', methods=['POST'])
@login_required
def api_add_diet():
    """Log a new diet entry"""
    data = request.get_json()
    
    diet = DietLog(
        user_id=current_user.id,
        food_name=data.get('food_name'),
        category=data.get('category'),
        calories=data.get('calories'),
        protein=data.get('protein'),
        fibre=data.get('fibre')
    )
    db.session.add(diet)
    db.session.commit()
    
    return jsonify({'message': 'Diet logged successfully', 'id': diet.id}), 201


@app.route('/api/diet/<int:diet_id>', methods=['DELETE'])
@login_required
def api_delete_diet(diet_id):
    """Delete a diet log"""
    diet = DietLog.query.get_or_404(diet_id)
    if diet.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(diet)
    db.session.commit()
    return jsonify({'message': 'Diet log deleted successfully'})


# --- Progress API ---

@app.route('/api/progress', methods=['GET'])
@login_required
def api_get_progress():
    """Get user's progress summary"""
    # Exercise stats
    total_exercises = ExerciseHistory.query.filter_by(user_id=current_user.id).count()
    total_calories = db.session.query(db.func.sum(ExerciseHistory.calories_burned))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    # Diet stats
    total_diet_logs = DietLog.query.filter_by(user_id=current_user.id).count()
    total_protein = db.session.query(db.func.sum(DietLog.protein))\
        .filter_by(user_id=current_user.id).scalar() or 0
    total_calories_consumed = db.session.query(db.func.sum(DietLog.calories))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    return jsonify({
        'exercise': {
            'total_sessions': total_exercises,
            'total_calories_burned': round(total_calories, 2)
        },
        'diet': {
            'total_logs': total_diet_logs,
            'total_protein': round(total_protein, 2),
            'total_calories_consumed': round(total_calories_consumed, 2)
        }
    })


# ==================== Database Initialization ====================

def create_database():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


# ==================== Run the App ====================

if __name__ == '__main__':
    # Create database tables
    create_database()
    
    print("Starting Virtual Trainer Application...")
    print(f"Base directory: {BASE_DIR}")
    print("\nAvailable routes:")
    print("  /               - Main landing page")
    print("  /register       - User registration")
    print("  /login          - User login")
    print("  /dashboard      - User dashboard (requires login)")
    print("  /index2.html    - Exercise training page")
    print("  /diet           - Diet recommendation system")
    print("\nAPI Endpoints:")
    print("  GET  /api/users           - List all users")
    print("  GET  /api/users/<id>      - Get user info")
    print("  GET  /api/exercises       - Get exercise history")
    print("  POST /api/exercises       - Log new exercise")
    print("  GET  /api/diet            - Get diet logs")
    print("  POST /api/diet            - Log new diet entry")
    print("  GET  /api/progress        - Get progress summary")
    print("\nStarting server on http://127.0.0.1:5000")
    
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)

