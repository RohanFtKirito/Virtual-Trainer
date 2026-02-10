# TODO: Fix Plank Form Score Logic

## Problem
Form Score always shows 100% even when user is not detected or has wrong posture.

## Solution
Update the form score logic in `exercise-plank.html` to dynamically update based on detection status:

### Changes Required:
1. **When pose NOT detected**: Set formScore = 0%
2. **When pose detected but wrong posture**: Set formScore = 40%
3. **When pose detected and perfect posture**: Set formScore = 100%

### File to Edit:
- `exercise-plank.html` (frontend JavaScript fix)

### Implementation Steps:
1. Initialize formScore to 0% on page load
2. Add explicit formScore update when pose is NOT detected
3. Add explicit formScore update when pose is detected but wrong posture
4. Update formScore display in all cases

## Status
- [x] Implement fix in exercise-plank.html

