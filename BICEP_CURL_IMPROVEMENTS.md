# Bicep Curl Rep Counting - Improvements Summary

**Date:** March 25, 2026
**File:** `exercise-bicepcurl.html`

---

## 🎯 Problem Statement

The original bicep curl implementation had several issues:
1. **Too lenient** - Single curl (up + down) was sometimes counted as 2 reps
2. **False positives** - Random hand movements triggered reps
3. **No stability validation** - State changes happened instantly on threshold crossing
4. **No direction validation** - Could oscillate between states without proper movement
5. **Time-based cooldown only** - Used milliseconds instead of frame counting

---

## ✅ What Was Changed

### **1. Implemented Proper 3-State Machine**

**Before:**
```javascript
let stage = 'down'; // Only 2 states: 'down' or 'up'
```

**After:**
```javascript
let stage = 'down'; // 3 states: 'down', 'up', 'transition'
```

**States:**
- **`down`** - Arm fully extended (angle > 150°)
- **`up`** - Arm fully contracted (angle < 50°)
- **`transition`** - Between positions (50° - 150°)

**Rep Counting Logic:**
- Reps ONLY counted when: `down → up → down` (complete cycle)
- Must complete full movement cycle for rep to count

---

### **2. Updated Angle Thresholds (User Specifications)**

**Before:**
```javascript
const SIDE_EXTENDED = 140;   // Too lenient
const SIDE_CONTRACTED = 60;  // Too lenient
const MIN_ANGLE_CHANGE = 50; // Too small, allowed half reps
```

**After:**
```javascript
const SIDE_EXTENDED = 150;   // Arm extended - angle > 150°
const SIDE_CONTRACTED = 50;  // Arm curled - angle < 50°
const MIN_ANGLE_RANGE = 90;  // Minimum range for valid rep (> 90°)
```

**Why This Matters:**
- **150° threshold** ensures arm is truly extended (not just partially)
- **50° threshold** ensures arm is truly curled (not just bent)
- **90° minimum range** prevents counting half reps or partial movements

---

### **3. Added Stability Check (Critical for Reducing False Positives)**

**New Variables:**
```javascript
let stableFrameCount = 0;           // Count consecutive stable frames
const STABILITY_FRAMES = 4;         // Require 4 stable frames before state change
```

**How It Works:**
```javascript
// Before changing state, must be stable for 4 consecutive frames
if (targetState === stage) {
    stableFrameCount++;  // Still in same state, increment
} else {
    // State change requested, check stability
    if (stableFrameCount >= STABILITY_FRAMES) {
        // OK to change state
        stage = targetState;
        stableFrameCount = 0;
    } else {
        // Not stable enough, stay in current state
        console.log(`⏸️ Not stable enough (${stableFrameCount}/${STABILITY_FRAMES})`);
    }
}
```

**Benefits:**
- Prevents noise/jitter from causing false state changes
- Requires sustained movement before counting
- Eliminates random hand movement triggers

---

### **4. Added Movement Direction Validation**

**New Variables:**
```javascript
let previousAngle = 0;         // Track previous angle
let angleDirection = 0;        // -1 = decreasing (up), 1 = increasing (down), 0 = neutral
let directionFrameCount = 0;   // Count consecutive frames with same direction
const DIRECTION_FRAMES = 3;    // Require 3 frames with consistent direction
```

**How It Works:**
```javascript
// Calculate movement direction
const angleDiff = angle - previousAngle;
let currentDirection = 0;

if (angleDiff > 2) {
    currentDirection = 1;  // Angle increasing (extending/down)
} else if (angleDiff < -2) {
    currentDirection = -1; // Angle decreasing (curling/up)
}

// Only change state if direction is consistent
if (directionFrameCount >= DIRECTION_FRAMES) {
    // Direction confirmed, allow state change
    stage = targetState;
} else {
    console.log(`⏸️ Direction not stable yet (${directionFrameCount}/${DIRECTION_FRAMES})`);
}
```

**Benefits:**
- Prevents oscillation between states
- Ensures movement is deliberate and consistent
- Blocks quick back-and-forth movements

---

### **5. Changed to Frame-Based Cooldown (Anti-Double Count)**

**Before:**
```javascript
let lastRepTime = 0;
const REP_COOLDOWN = 700;  // milliseconds
if (now - lastRepTime > REP_COOLDOWN) {
    // Count rep
}
```

**After:**
```javascript
let cooldownFrames = 0;
const COOLDOWN_FRAME_COUNT = 12;  // 12 frames (~400ms at 30fps)

if (cooldownFrames > 0) {
    cooldownFrames--;  // Decrement each frame
    // Skip processing
} else {
    // Count rep and start cooldown
    cooldownFrames = COOLDOWN_FRAME_COUNT;
}
```

**Why This Is Better:**
- Frame-based is more consistent across different frame rates
- 12 frames at 30fps = ~400ms (sufficient to prevent double counting)
- Clear visual feedback during cooldown

---

### **6. Added Minimum Range Check**

**New Variables:**
```javascript
let repMinAngle = 180;  // Track max angle during rep (most extended)
let repMaxAngle = 0;    // Track min angle during rep (most curled)
let repInProgress = false;  // Flag to track if rep cycle has started
```

**How It Works:**
```javascript
// Track angle during rep cycle
if (repInProgress) {
    if (angle < repMinAngle) repMinAngle = angle;  // Most curled
    if (angle > repMaxAngle) repMaxAngle = angle;  // Most extended
}

// When completing cycle, validate range
if (previousState === 'up' && stage === 'down' && repInProgress) {
    const repRange = repMaxAngle - repMinAngle;

    if (repRange >= MIN_ANGLE_RANGE) {  // Must be > 90°
        // Valid rep, count it
    } else {
        console.log(`⚠️ Partial rep: ${Math.round(repRange)}° (need ${MIN_ANGLE_RANGE}°)`);
    }
}
```

**Benefits:**
- Prevents counting partial/half reps
- Ensures full range of motion
- Only counts complete bicep curls

---

### **7. Relaxed Elbow Constraint**

**Before:**
```javascript
const ELBOW_MOVEMENT_THRESHOLD = 0.05;  // ~5-10 pixels - too strict
```

**After:**
```javascript
const ELBOW_MOVEMENT_THRESHOLD = 0.08;  // ~15-20 pixels - relaxed
```

**Feedback Changed:**
```javascript
// Before: Could block reps
if (!elbowStable) {
    // Block rep
}

// After: Warning only, doesn't block
if (!elbowStable) {
    console.log('⚠️ Elbow movement detected (not blocking rep)');
    feedbackOverlayEl.textContent = '⚠️ Keep elbow steady (relaxed)';
    feedbackOverlayEl.className = 'warning';
}
```

**Benefits:**
- More forgiving for natural body movement
- Doesn't frustrate users with strict form requirements
- Still provides feedback for improvement

---

### **8. Enhanced Debug Logging**

**Console Logs Now Show:**
```javascript
console.log(
    'Angle:', Math.round(angle), '° |',
    'State:', stage, '|',
    'Direction:', currentDirection === 1 ? 'DOWN↓' : currentDirection === -1 ? 'UP↑' : '—',
    '| Stable:', stableFrameCount,
    '| Cooldown:', cooldownFrames,
    '| Reps:', repCount
);
```

**Example Output:**
```
Angle: 165° | State: down | Direction: — | Stable: 5 | Cooldown: 0 | Reps: 0
Angle: 158° | State: down | Direction: UP↑ | Stable: 6 | Cooldown: 0 | Reps: 0
Angle: 142° | State: transition | Direction: UP↑ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 125° | State: transition | Direction: UP↑ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 98°  | State: transition | Direction: UP↑ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 72°  | State: transition | Direction: UP↑ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 45°  | State: up | Direction: UP↑ | Stable: 1 | Cooldown: 0 | Reps: 0
Angle: 42°  | State: up | Direction: — | Stable: 2 | Cooldown: 0 | Reps: 0
Angle: 44°  | State: up | Direction: — | Stable: 3 | Cooldown: 0 | Reps: 0
Angle: 43°  | State: up | Direction: — | Stable: 4 | Cooldown: 0 | Reps: 0
Angle: 48°  | State: transition | Direction: DOWN↓ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 65°  | State: transition | Direction: DOWN↓ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 92°  | State: transition | Direction: DOWN↓ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 128° | State: transition | Direction: DOWN↓ | Stable: 0 | Cooldown: 0 | Reps: 0
Angle: 155° | State: down | Direction: DOWN↓ | Stable: 1 | Cooldown: 0 | Reps: 0
🔄 STATE: up → down (dir: 8 frames)
✅ REP COUNTED! #1 | Range: 113°
```

---

## 📊 New Thresholds Summary

| Parameter | Old Value | New Value | Purpose |
|-----------|-----------|-----------|---------|
| `SIDE_EXTENDED` | 140° | **150°** | Arm extended threshold |
| `SIDE_CONTRACTED` | 60° | **50°** | Arm curled threshold |
| `MIN_ANGLE_RANGE` | 50° | **90°** | Minimum range for valid rep |
| `STABILITY_FRAMES` | N/A | **4** | Frames required for stable state |
| `DIRECTION_FRAMES` | N/A | **3** | Frames required for consistent direction |
| `COOLDOWN_FRAMES` | 700ms | **12** | Frame-based cooldown (~400ms) |
| `ELBOW_THRESHOLD` | 0.05 | **0.08** | Relaxed elbow tolerance |

---

## 🎯 How Double Counting Was Prevented

### **1. Frame-Based Cooldown**
```javascript
if (cooldownFrames > 0) {
    cooldownFrames--;  // Skip processing for 12 frames
    stageDisplay.textContent = `COOLDOWN (${cooldownFrames})`;
}
```
- After counting a rep, system ignores input for 12 frames (~400ms)
- Prevents immediate recount on same movement

### **2. State Cycle Requirement**
```javascript
// Only count when: down → up → down
if (previousState === 'up' && stage === 'down' && repInProgress) {
    // Count rep
}
```
- Must complete FULL cycle for rep to count
- Can't count same curl twice

### **3. Minimum Range Validation**
```javascript
if (repRange >= MIN_ANGLE_RANGE) {  // Must be > 90°
    // Valid rep
}
```
- Prevents counting partial movements
- Ensures full range of motion

### **4. Stability + Direction Gates**
```javascript
if (stableFrameCount >= STABILITY_FRAMES) {
    if (directionFrameCount >= DIRECTION_FRAMES) {
        // Both confirmed, allow state change
    }
}
```
- Two-layer validation before any state change
- Prevents oscillation and false triggers

---

## 🚀 Expected Results

### **Before:**
- ❌ Single curl sometimes counted as 2 reps
- ❌ Random hand movements triggered reps
- ❌ Partial reps counted
- ❌ No feedback on what's happening

### **After:**
- ✅ **Clean rep counting** - 1 curl = 1 rep (down → up → down)
- ✅ **No double counting** - Frame cooldown prevents immediate recount
- ✅ **Reduced false positives** - Stability check blocks noise
- ✅ **Full range required** - 90° minimum prevents half reps
- ✅ **Direction validation** - Prevents oscillation
- ✅ **Smooth experience** - Relaxed elbow tolerance
- ✅ **Clear debugging** - Console logs show state, direction, stability

---

## 📝 Testing Checklist

To verify the improvements:

1. **Test single curl:**
   - [ ] Curl up and down once → Should count as exactly 1 rep
   - [ ] Check console for "down → transition → up → transition → down" cycle

2. **Test partial movements:**
   - [ ] Curl halfway and return → Should NOT count
   - [ ] Quick small movements → Should NOT count

3. **Test double counting prevention:**
   - [ ] Hold arm at bottom after rep → Should NOT count again
   - [ ] Wait for cooldown to finish → Can count next rep

4. **Test stability:**
   - [ ] Shake arm randomly → Should NOT trigger state change
   - [ ] Make deliberate movement → Should count after stability confirmed

5. **Test front vs side view:**
   - [ ] Both views should use similar state machine logic
   - [ ] Reps should count consistently in both views

---

## 🎛️ Tuning Parameters (If Needed)

If the system is still too lenient/strict, adjust these:

```javascript
// Make STRICTER (reduce false positives):
const STABILITY_FRAMES = 5;        // Increase from 4
const DIRECTION_FRAMES = 4;        // Increase from 3
const MIN_ANGLE_RANGE = 100;       // Increase from 90
const COOLDOWN_FRAME_COUNT = 15;   // Increase from 12

// Make MORE LENIENT (better for beginners):
const STABILITY_FRAMES = 3;        // Decrease from 4
const DIRECTION_FRAMES = 2;        // Decrease from 3
const MIN_ANGLE_RANGE = 80;        // Decrease from 90
const COOLDOWN_FRAME_COUNT = 10;   // Decrease from 12
```

---

## 📚 Technical Notes

### **State Machine Flow:**
```
START
  ↓
[down: angle > 150°]
  ↓ (stable 4 frames + consistent direction)
[transition: 50° < angle < 150°]
  ↓ (stable 4 frames + consistent direction)
[up: angle < 50°]
  ↓ (stable 4 frames + consistent direction)
[transition: 50° < angle < 150°]
  ↓ (stable 4 frames + consistent direction)
[down: angle > 150°]
  ↓
✅ REP COUNTED! (if range > 90°)
  ↓
[Cooldown: 12 frames]
  ↓
Ready for next rep
```

### **Frame Rate Considerations:**
- Assumes ~30 FPS webcam
- 4 stability frames = ~133ms of sustained movement
- 12 cooldown frames = ~400ms of no counting
- 3 direction frames = ~100ms of consistent direction

---

**Document Version:** 1.0
**Last Updated:** March 25, 2026
