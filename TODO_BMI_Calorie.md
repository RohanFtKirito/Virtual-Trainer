# TODO: BMI and Maintenance Calorie Calculation Implementation

## Task: Add BMI and maintenance calorie calculation to diet recommendation system

### ✅ Implementation Complete:

#### Backend Changes (app.py):
- [x] Added `/diet/calculate` route for BMI, BMR, and maintenance calorie calculations
- [x] Returns render_template() with variables (not JSON)
- [x] Calculates BMI, BMR, Maintenance Calories, Protein Required

#### Frontend Changes (diet-mainpage.html):
- [x] **Layout Order Fixed:**
  1. BMI & Calorie Calculator (TOP)
  2. BMI Result Section
  3. Predict Diet Category Section
  4. Diet Recommendation Result
  5. Food Categories (Muscle Gain, Weight Gain, Weight Loss)

- [x] **Spacing Fixed:**
  - Added CSS class `.bmi-form-row` for first row (Height | Weight | Age)
  - Added CSS class `.gender-section` for Gender row with proper margin
  - Gender section on separate line with margin-top: 15px

- [x] **Form Submission:**
  - Uses normal Flask POST form submission (not AJAX)
  - Shows "Calculating..." via JavaScript onclick handler
  - Button disables during form submission

- [x] **Results Display:**
  - Shows results using Jinja2 templates on same page
  - Displays: BMI, BMI Category, BMR, Maintenance Calories, Protein Required

### Calculations:
- BMI = weight (kg) / (height_m)²
- BMR (Mifflin-St Jeor):
  - Male: (10 × weight) + (6.25 × height_cm) - (5 × age) + 5
  - Female: (10 × weight) + (6.25 × height_cm) - (5 × age) - 161
- Maintenance Calories = BMR × 1.55
- Protein Required = weight (kg) × 1.6 g/day

### Files Modified:
1. `/Users/rohanmhatre/Desktop/Virtual Trainer/app.py` - calculate_bmi_calories() route
2. `/Users/rohanmhatre/Desktop/Virtual Trainer/diet-mainpage.html` - Full layout with proper order and spacing

