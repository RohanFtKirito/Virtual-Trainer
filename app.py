"""
Unified Flask Application for Virtual Trainer
Combines pose detection website and diet recommendation system
Features: User authentication, database storage, REST API endpoints
"""

# Force Python 3.11 on Render via runtime.txt - deployed March 24, 2026
print("=" * 60)
print("RENDER PYTHON FIX DEPLOYED - Using Python 3.11.9")
print("This deployment forces Python 3.11 for pandas compatibility")
print("=" * 60)

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from datetime import datetime
import pickle
import pandas as pd
import csv
import os

# ==================== Flask Configuration ====================
app = Flask(__name__, template_folder='.', static_folder='assets')

# Enable CORS for all routes
CORS(app)

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


# ==================== Unified Exercise Detail Routes ====================

# Exercise data structure
EXERCISES = {
    'bicepcurl': {
        'title': 'Bicep Curl',
        'category': 'weight-gain',
        'category_title': 'Weight Gain',
        'description': 'Isolate and build your biceps with this fundamental arm exercise. Great for beginners starting strength training.',
        'youtube_id': 'ykJmrZ5v0Oo',
        'difficulty': 'Beginner',
        'duration': '10 min',
        'has_ai': True,
        'ai_type': 'bicepcurl',
        'stat_label': 'Rep Count',
        'stat_unit': 'reps',
        'instructions': [
            'Stand with feet shoulder-width apart',
            'Hold weights in both hands',
            'Curl arms up, bending at elbows',
            'Lower back down slowly',
            'Keep your back straight',
            'Press Q to stop camera'
        ]
    },
    'pushup': {
        'title': 'Push-Up',
        'category': 'weight-gain',
        'category_title': 'Weight Gain',
        'description': 'Classic bodyweight exercise that targets chest, shoulders, and triceps. Build upper body strength without equipment.',
        'youtube_id': 'IODxDxX7oi4',
        'difficulty': 'Beginner',
        'duration': '15 min',
        'has_ai': True,
        'ai_type': 'pushup',
        'stat_label': 'Rep Count',
        'stat_unit': 'reps',
        'instructions': [
            'Start in plank position',
            'Place hands shoulder-width apart',
            'Lower chest to ground',
            'Push back up to starting',
            'Keep core engaged',
            'Press Q to stop camera'
        ]
    },
    'plank': {
        'title': 'Plank',
        'category': 'weight-loss',
        'category_title': 'Weight Loss',
        'description': 'Isometric core exercise that strengthens abs, back, and shoulders. Build stability and burn calories effectively.',
        'youtube_id': 'ASdvN_XEl_c',
        'difficulty': 'Beginner',
        'duration': '30-60 sec',
        'has_ai': True,
        'ai_type': 'plank',
        'stat_label': 'Hold Duration',
        'stat_unit': 'time',
        'instructions': [
            'Start face down on floor',
            'Rest on forearms and toes',
            'Keep body in straight line',
            'Engage your core muscles',
            'Hold position, don\'t sag hips',
            'Press Q to stop camera'
        ]
    },
    'squats': {
        'title': 'Squats',
        'category': 'weight-gain',
        'category_title': 'Weight Gain',
        'description': 'King of leg exercises! Build powerful quads, glutes, and hamstrings. Essential for lower body development.',
        'youtube_id': 'ultWZbUMPL8',
        'difficulty': 'Beginner',
        'duration': '15 min',
        'has_ai': False,
        'instructions': [
            'Stand with feet shoulder-width apart',
            'Keep chest up and core engaged',
            'Lower down by bending knees',
            'Push through heels to stand up',
            'Keep knees in line with toes',
            'Start with bodyweight, add weight as needed'
        ]
    },
    'benchpress': {
        'title': 'Bench Press',
        'category': 'weight-gain',
        'category_title': 'Weight Gain',
        'description': 'Compound movement for building chest mass and strength. The ultimate upper body pushing exercise.',
        'youtube_id': 'gRVjAtPip0Y',
        'difficulty': 'Intermediate',
        'duration': '20 min',
        'has_ai': False,
        'instructions': [
            'Lie flat on bench with feet on floor',
            'Grip bar slightly wider than shoulders',
            'Lower bar to chest with control',
            'Press up until arms are extended',
            'Keep shoulder blades retracted',
            'Use a spotter for heavy weights'
        ]
    },
    'deadlift': {
        'title': 'Deadlift',
        'category': 'weight-gain',
        'category_title': 'Weight Gain',
        'description': 'The ultimate strength builder! Works your entire posterior chain. Builds serious muscle and total body power.',
        'youtube_id': 'op9kVnSso6Q',
        'difficulty': 'Advanced',
        'duration': '25 min',
        'has_ai': False,
        'instructions': [
            'Stand with feet hip-width apart',
            'Grip bar with hands just outside legs',
            'Keep back straight, bend at hips',
            'Drive through heels to stand up',
            'Pull shoulder blades together at top',
            'Lower with control, maintain form'
        ]
    },
    'jumpingjacks': {
        'title': 'Jumping Jacks',
        'category': 'weight-loss',
        'category_title': 'Weight Loss',
        'description': 'Classic full-body cardio exercise that elevates heart rate and burns calories. Perfect warm-up or HIIT component.',
        'youtube_id': 'dmMwK4OoUjM',
        'difficulty': 'Beginner',
        'duration': '10 min',
        'has_ai': False,
        'instructions': [
            'Stand with feet together, arms at sides',
            'Jump while spreading legs and raising arms',
            'Jump again to return to start',
            'Maintain steady rhythm',
            'Land softly on balls of feet',
            'Breathe rhythmically throughout'
        ]
    },
    'burpees': {
        'title': 'Burpees',
        'category': 'weight-loss',
        'category_title': 'Weight Loss',
        'description': 'The ultimate fat-burning exercise! Combines squat, push-up, and jump for maximum calorie burn in minimal time.',
        'youtube_id': 'TU8DffXiTME',
        'difficulty': 'Intermediate',
        'duration': '15 min',
        'has_ai': False,
        'instructions': [
            'Start in standing position',
            'Drop into squat position',
            'Place hands on floor and jump feet back',
            'Do a push-up',
            'Jump feet back to hands',
            'Explode up with arms overhead'
        ]
    },
    'mountainclimbers': {
        'title': 'Mountain Climbers',
        'category': 'weight-loss',
        'category_title': 'Weight Loss',
        'description': 'Dynamic core exercise that also provides cardio benefits. Engages multiple muscle groups while burning fat.',
        'youtube_id': 'nmwgirgXLYM',
        'difficulty': 'Intermediate',
        'duration': '15 min',
        'has_ai': False,
        'instructions': [
            'Start in high plank position',
            'Drive one knee toward chest',
            'Quickly switch legs while maintaining plank',
            'Keep core tight throughout',
            'Move as quickly as possible',
            'Maintain steady breathing'
        ]
    },
    'highknees': {
        'title': 'High Knees',
        'category': 'weight-loss',
        'category_title': 'Weight Loss',
        'description': 'High-intensity cardio move that elevates heart rate quickly. Great for burning calories and improving leg endurance.',
        'youtube_id': 'A5vhbOcJLyA',
        'difficulty': 'Beginner',
        'duration': '10 min',
        'has_ai': False,
        'instructions': [
            'Stand with feet hip-width apart',
            'Lift one knee toward chest',
            'Quickly switch to other knee',
            'Move as quickly as possible',
            'Land on balls of feet',
            'Pump arms while driving knees'
        ]
    }
}


@app.route('/exercise/<exercise_name>')
def exercise_detail(exercise_name):
    """Unified exercise detail page with AI training and tutorial"""
    exercise_key = exercise_name.lower().replace('-', '').replace(' ', '')

    if exercise_key not in EXERCISES:
        return redirect(url_for('courses'))

    exercise = EXERCISES[exercise_key]

    # Load appropriate AI script if needed
    if exercise['has_ai']:
        # Load AI-specific script
        ai_scripts = {
            'bicepcurl': open(os.path.join(BASE_DIR, 'ai_scripts', 'bicepcurl.js')).read() if os.path.exists(os.path.join(BASE_DIR, 'ai_scripts', 'bicepcurl.js')) else '',
            'pushup': open(os.path.join(BASE_DIR, 'ai_scripts', 'pushup.js')).read() if os.path.exists(os.path.join(BASE_DIR, 'ai_scripts', 'pushup.js')) else '',
            'plank': open(os.path.join(BASE_DIR, 'ai_scripts', 'plank.js')).read() if os.path.exists(os.path.join(BASE_DIR, 'ai_scripts', 'plank.js')) else ''
        }
        exercise['ai_script'] = ai_scripts.get(exercise['ai_type'], '')

    return render_template('exercise-detail.html', exercise=exercise)


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
    """Predict diet category based on macros using rule-based logic with Indian diet context"""
    try:
        calories = float(request.form['input_1'])  # Calories
        protein = float(request.form['input_2'])  # Protein (g)

        # Rule-based recommendation logic
        # Calculate protein per 100 calories
        protein_per_100cal = (protein / calories) * 100 if calories > 0 else 0

        # Classification rules
        if calories < 150 and protein_per_100cal > 8:
            result = 'Weight Loss'
        elif calories > 250 or (calories > 180 and protein_per_100cal > 6):
            result = 'Weight Gain'
        elif protein_per_100cal > 7:
            result = 'Weight Gain'  # High protein foods good for gaining
        elif calories < 200 and protein_per_100cal < 5:
            result = 'Weight Loss'  # Lower calorie, moderate protein
        else:
            result = 'Weight Loss'  # Default to weight loss for general health

        return render_template('diet-mainpage.html', result=result)
    except Exception as e:
        return render_template('diet-mainpage.html', result=f'Error: {str(e)}')


@app.route('/diet/analyze', methods=['POST'])
def diet_analyze():
    """Goal-based intelligent diet analysis system with scoring"""
    try:
        calories = float(request.form['input_1'])  # Calories
        protein = float(request.form['input_2'])  # Protein (g)
        fat = float(request.form['input_3'])  # Fat (g)
        goal = request.form['goal']  # weight_gain, weight_loss, maintenance

        # Calculate macro ratios
        protein_calories = protein * 4
        fat_calories = fat * 9
        total_calories = calories if calories > 0 else 1

        protein_ratio = (protein_calories / total_calories) * 100
        fat_ratio = (fat_calories / total_calories) * 100

        # Initialize score and analysis
        score = 50  # Base score
        analysis = []
        suggestions = []
        quick_fix = ""

        # Goal-based analysis logic
        if goal == 'weight_gain':
            # WEIGHT GAIN: Prioritize high protein, adequate calories, moderate fat
            if protein_ratio >= 25:
                score += 20
                analysis.append("Protein: Excellent ✅")
            elif protein_ratio >= 20:
                score += 10
                analysis.append("Protein: Good ✅")
            else:
                score -= 10
                analysis.append("Protein: Low ❌")
                suggestions.append("Increase protein intake with eggs, paneer, chicken")
                quick_fix = "Add 2 eggs or 100g paneer to your meal today"

            if calories >= 300:
                score += 15
                analysis.append("Calories: Excellent ✅")
            elif calories >= 200:
                score += 10
                analysis.append("Calories: Good ✅")
            else:
                score -= 15
                analysis.append("Calories: Too Low ❌")
                suggestions.append("Add calorie-dense foods like nuts, ghee, bananas")
                if not quick_fix:
                    quick_fix = "Add 2 bananas with peanut butter to breakfast"

            if fat_ratio >= 20 and fat_ratio <= 35:
                score += 10
                analysis.append("Fat: Optimal ✅")
            elif fat_ratio > 35:
                score -= 5
                analysis.append("Fat: High ⚠️")
                suggestions.append("Reduce excessive fried foods and oils")
            else:
                analysis.append("Fat: Low ⚠️")
                suggestions.append("Add healthy fats like ghee, olive oil, nuts")

            if not quick_fix:
                quick_fix = "Increase portion sizes by 25% for better weight gain"

        elif goal == 'weight_loss':
            # WEIGHT LOSS: Prioritize low calories, high protein, low fat
            if protein_ratio >= 30:
                score += 20
                analysis.append("Protein: Excellent ✅")
            elif protein_ratio >= 25:
                score += 15
                analysis.append("Protein: Good ✅")
            elif protein_ratio >= 20:
                score += 5
                analysis.append("Protein: Moderate ⚠️")
            else:
                score -= 10
                analysis.append("Protein: Low ❌")
                suggestions.append("Increase lean protein like dal, paneer, chicken breast")
                quick_fix = "Replace one carb serving with protein-rich food"

            if calories <= 150:
                score += 20
                analysis.append("Calories: Excellent ✅")
            elif calories <= 200:
                score += 10
                analysis.append("Calories: Good ✅")
            elif calories <= 250:
                score += 5
                analysis.append("Calories: Moderate ⚠️")
            else:
                score -= 20
                analysis.append("Calories: Too High ❌")
                suggestions.append("Reduce portion sizes and avoid calorie-dense foods")
                if not quick_fix:
                    quick_fix = "Replace rice/chapati with extra vegetables and protein"

            if fat_ratio <= 15:
                score += 15
                analysis.append("Fat: Excellent ✅")
            elif fat_ratio <= 20:
                score += 10
                analysis.append("Fat: Good ✅")
            elif fat_ratio <= 25:
                score -= 5
                analysis.append("Fat: Moderate ⚠️")
            else:
                score -= 15
                analysis.append("Fat: High ❌")
                suggestions.append("Cut down on fried foods, ghee, and oily curries")
                if not quick_fix:
                    quick_fix = "Use 1 tsp less oil/ghee in cooking today"

            if not quick_fix:
                quick_fix = "Fill half your plate with vegetables to stay full longer"

        else:  # maintenance
            # MAINTENANCE: Balanced macros
            if protein_ratio >= 20 and protein_ratio <= 30:
                score += 20
                analysis.append("Protein: Balanced ✅")
            elif protein_ratio >= 15:
                score += 10
                analysis.append("Protein: Adequate ⚠️")
            else:
                score -= 10
                analysis.append("Protein: Low ❌")
                suggestions.append("Aim for 20-30% calories from protein")
                quick_fix = "Include protein in every meal (dal, paneer, eggs)"

            if calories >= 200 and calories <= 300:
                score += 20
                analysis.append("Calories: Balanced ✅")
            elif calories >= 150:
                score += 10
                analysis.append("Calories: Adequate ⚠️")
            else:
                score -= 10
                analysis.append("Calories: Unbalanced ❌")

            if fat_ratio >= 20 and fat_ratio <= 30:
                score += 15
                analysis.append("Fat: Balanced ✅")
            elif fat_ratio >= 15 and fat_ratio <= 35:
                score += 5
                analysis.append("Fat: Adequate ⚠️")
            else:
                score -= 10
                analysis.append("Fat: Unbalanced ❌")
                suggestions.append("Aim for 20-30% calories from healthy fats")

            if not quick_fix:
                quick_fix = "Follow the plate rule: 1/2 veggies, 1/4 protein, 1/4 carbs"

        # Add default suggestions if none
        if not suggestions:
            suggestions = [
                "Continue with your current balanced approach",
                "Stay hydrated and eat regular meals"
            ]

        # Ensure score is within 0-100 range
        score = max(0, min(100, score))

        # Generate score message
        if score >= 80:
            score_message = "Excellent! Your diet is well-aligned with your goal."
        elif score >= 60:
            score_message = "Good! Some improvements can optimize your diet."
        elif score >= 40:
            score_message = "Fair. Your diet needs some adjustments."
        else:
            score_message = "Poor. Significant changes needed to reach your goal."

        analysis_result = {
            'score': score,
            'score_message': score_message,
            'analysis': analysis,
            'suggestions': suggestions,
            'quick_fix': quick_fix
        }

        return render_template('diet-mainpage.html', analysis_result=analysis_result)

    except Exception as e:
        return render_template('diet-mainpage.html', analysis_result={
            'score': 0,
            'score_message': f"Error: {str(e)}",
            'analysis': ["Error in analysis"],
            'suggestions': ["Please check your inputs"],
            'quick_fix': "Try again with valid values"
        })


@app.route('/diet/weightgain', methods=['POST'])
def weightgain():
    """Filter weight gain foods with Indian diet recommendations"""
    # Indian diet recommendations for weight gain
    indian_weight_gain = [
        "Rice (Brown/White) - High calorie staple",
        "Banana - Energy-rich fruit",
        "Peanut Butter - Calorie-dense healthy fat",
        "Paneer (Cottage Cheese) - High protein vegetarian option",
        "Milk (Full Cream) - Protein and calories",
        "Chicken Breast - Lean protein source",
        "Potato - High carb, calorie-dense",
        "Dry Fruits (Almonds, Cashews) - Healthy calorie boost",
        "Ghee (Clarified Butter) - Healthy fats for weight gain",
        "Eggs - Complete protein source"
    ]

    vegetarian_foods = [
        "Rice (Brown/White) - High calorie staple",
        "Banana - Energy-rich fruit",
        "Peanut Butter - Calorie-dense healthy fat",
        "Paneer (Cottage Cheese) - High protein vegetarian option",
        "Milk (Full Cream) - Protein and calories",
        "Potato - High carb, calorie-dense",
        "Dry Fruits (Almonds, Cashews) - Healthy calorie boost",
        "Ghee (Clarified Butter) - Healthy fats for weight gain",
        "Dal (Lentils) - Protein-rich Indian staple",
        "Cheese - High calorie protein source"
    ]

    try:
        vegetarian = request.form.getlist('vegetarian')

        if 'vegetarian' in vegetarian:
            selected_foods = vegetarian_foods
        else:
            selected_foods = indian_weight_gain

        # Return 5 random recommendations
        import random
        recommendations = random.sample(selected_foods, min(5, len(selected_foods)))
        weightgainfoods = '\n'.join(recommendations)

        return render_template('diet-mainpage.html', weightgainfoods=weightgainfoods)
    except Exception as e:
        return render_template('diet-mainpage.html', weightgainfoods=f'Error: {str(e)}')


@app.route('/diet/weightloss', methods=['POST'])
def weightloss():
    """Filter weight loss foods with Indian diet recommendations"""
    # Indian diet recommendations for weight loss
    indian_weight_loss = [
        "Oats - High fiber, keeps you full longer",
        "Brown Rice - Low GI, complex carbs",
        "Dal (Lentils) - High protein, fiber-rich",
        "Paneer (Low Fat) - High protein, low calorie",
        "Boiled Eggs - Protein-rich, low calorie",
        "Chicken Breast - Lean protein for fat loss",
        "Roti (Whole Wheat) - Controlled portion",
        "Green Vegetables (Spinach, Broccoli) - Low calorie, nutrient-dense",
        "Curd/Yogurt (Low Fat) - Probiotics + protein",
        "Moong Dal - Easy to digest, high protein"
    ]

    vegetarian_foods = [
        "Oats - High fiber, keeps you full longer",
        "Brown Rice - Low GI, complex carbs",
        "Dal (Lentils) - High protein, fiber-rich",
        "Paneer (Low Fat) - High protein, low calorie",
        "Roti (Whole Wheat) - Controlled portion",
        "Green Vegetables (Spinach, Broccoli) - Low calorie, nutrient-dense",
        "Curd/Yogurt (Low Fat) - Probiotics + protein",
        "Moong Dal - Easy to digest, high protein",
        "Sprouts (Moong, Chickpea) - High fiber, protein",
        "Buttermilk - Low calorie, aids digestion"
    ]

    try:
        vegetarian = request.form.getlist('vegetarian')

        if 'vegetarian' in vegetarian:
            selected_foods = vegetarian_foods
        else:
            selected_foods = indian_weight_loss

        # Return 5 random recommendations
        import random
        recommendations = random.sample(selected_foods, min(5, len(selected_foods)))
        weightlossfoods = '\n'.join(recommendations)

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


@app.route('/diet/calculate', methods=['POST'])
def calculate_bmi_calories():
    """Calculate BMI, BMR, maintenance calories, and protein requirement"""
    try:
        # Get user inputs
        height_cm = float(request.form['height'])
        weight_kg = float(request.form['weight'])
        age = int(request.form['age'])
        gender = request.form['gender']
        
        # Calculate BMI
        height_m = height_cm / 100  # Convert cm to meters
        bmi = weight_kg / (height_m ** 2)
        
        # Calculate BMR using Mifflin-St Jeor Equation
        if gender.lower() == 'male':
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
        # Calculate maintenance calories (moderate activity level)
        maintenance_calories = bmr * 1.55
        
        # Calculate protein required (grams) = weight (kg) × 1.6
        protein_required = weight_kg * 1.6
        
        # Determine BMI category
        if bmi < 18.5:
            bmi_category = 'Underweight'
        elif 18.5 <= bmi <= 24.9:
            bmi_category = 'Normal'
        elif 25 <= bmi <= 29.9:
            bmi_category = 'Overweight'
        else:
            bmi_category = 'Obese'
        
        # Render results on same page
        return render_template('diet-mainpage.html', 
                               bmi_result=True,
                               bmi_value=round(bmi, 2),
                               bmi_category=bmi_category,
                               maintenance_calories=round(maintenance_calories, 2),
                               bmr_value=round(bmr, 2),
                               protein_required=round(protein_required, 2))
    except Exception as e:
        return render_template('diet-mainpage.html', 
                               bmi_result=True,
                               error=f'Error calculating: {str(e)}')


# ==================== REST API Endpoints ====================

# --- Users API ---

@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users (admin only)"""
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("API HIT:", request.path)
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
    print("\nStarting server on http://0.0.0.0:10000")
    print("Render deployment: Using PORT environment variable")

    # Render deployment: Bind to 0.0.0.0 and use PORT from environment
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)

