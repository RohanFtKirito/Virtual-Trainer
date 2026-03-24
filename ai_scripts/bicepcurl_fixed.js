// ==================== BICEP CURL DETECTION SCRIPT (FIXED & OPTIMIZED) ====================
// Version: 2.0 - Production Ready
// Issues Fixed: Unrealistic thresholds, stage confusion, no debugging

// ==================== CONFIGURATION ====================
const CONFIG = {
    // Angle thresholds (realistic for bicep curl)
    DOWN_ANGLE_MAX: 70,      // Arm curled (elbow bent)
    UP_ANGLE_MIN: 130,       // Arm extended (elbow straight)

    // Smoothing & debouncing
    SMOOTHING_WINDOW: 3,     // Rolling average window (reduces noise)
    DEBOUNCE_TIME: 300,      // Min time between reps (ms) - prevents false reps

    // Visibility
    MIN_VISIBILITY: 0.5      // Minimum landmark visibility
};

// ==================== STATE VARIABLES ====================
let repCount = 0;
let stage = 'down';          // Start in 'down' position (arm curled)
let lastRepTime = 0;         // Debounce: timestamp of last rep

// Angle smoothing buffer
let angleBuffer = [];         // Store recent angles for smoothing
let currentAngle = 0;         // Current smoothed angle

// ==================== SPEECH SYNTHESIS ====================
const synth = window.speechSynthesis;

function speak(text) {
    if (synth.speaking) return;
    const utterance = new SpeechSynthesisUtterance(String(text));
    utterance.rate = 1.2;
    utterance.pitch = 1.0;
    synth.speak(utterance);
}

// ==================== ANGLE CALCULATION ====================
function calculateAngle(a, b, c) {
    const radians = Math.atan2(c.y - b.y, c.x - b.x) -
                    Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}

// ==================== ANGLE SMOOTHING ====================
function smoothAngle(newAngle) {
    angleBuffer.push(newAngle);

    // Keep buffer at configured size
    if (angleBuffer.length > CONFIG.SMOOTHING_WINDOW) {
        angleBuffer.shift();
    }

    // Calculate rolling average
    const sum = angleBuffer.reduce((a, b) => a + b, 0);
    return sum / angleBuffer.length;
}

// ==================== REP COUNTING LOGIC ====================
function countRep() {
    const now = Date.now();

    // Debounce: Prevent counting reps too quickly
    if (now - lastRepTime < CONFIG.DEBOUNCE_TIME) {
        console.log('⚠️ Rep too fast, debouncing...');
        return false;
    }

    repCount++;
    lastRepTime = now;

    console.log('✅ REP COUNTED!', repCount);
    console.log('---');

    return true;
}

// ==================== MAIN DETECTION FUNCTION ====================
function detectBicepCup(landmarks, canvasCtx, canvasElement) {
    // Get landmarks for both arms
    const leftShoulder = landmarks[11];
    const leftElbow = landmarks[13];
    const leftWrist = landmarks[15];
    const rightShoulder = landmarks[12];
    const rightElbow = landmarks[14];
    const rightWrist = landmarks[16];

    // Check visibility
    const isVisible = leftShoulder.visibility > CONFIG.MIN_VISIBILITY &&
                      leftElbow.visibility > CONFIG.MIN_VISIBILITY &&
                      leftWrist.visibility > CONFIG.MIN_VISIBILITY;

    if (!isVisible) {
        console.log('❌ Person not fully visible');
        if (typeof updateFeedback === 'function') {
            updateFeedback('warning', 'Move into frame');
        }
        if (typeof statusDisplay !== 'undefined') {
            statusDisplay.textContent = 'Not Detected';
        }
        return;
    }

    // Calculate angles for both arms
    const leftAngle = calculateAngle(leftShoulder, leftElbow, leftWrist);
    const rightAngle = calculateAngle(rightShoulder, rightElbow, rightWrist);

    // Average both arms
    const rawAngle = (leftAngle + rightAngle) / 2;

    // Smooth the angle (reduces noise/jitter)
    currentAngle = smoothAngle(rawAngle);

    // ==================== DEBUGGING ====================
    console.log('📊 Angle Data:');
    console.log('  Raw Angle:', rawAngle.toFixed(1) + '°');
    console.log('  Smoothed Angle:', currentAngle.toFixed(1) + '°');
    console.log('  Current Stage:', stage);
    console.log('  Rep Count:', repCount);

    // ==================== STATE MACHINE ====================
    const previousStage = stage;

    if (currentAngle < CONFIG.DOWN_ANGLE_MAX) {
        // Arm is curled (DOWN position)
        stage = 'down';
        console.log('  ↘️ Arm CURLING (down)');

    } else if (currentAngle > CONFIG.UP_ANGLE_MIN) {
        // Arm is extended (UP position)
        if (stage === 'down') {
            // Transition: down → up (ready to count rep on next curl)
            stage = 'up';
            console.log('  ↕️ Arm EXTENDING (up)');
        }
    }

    // ==================== COUNT REP ====================
    // Count rep when: arm goes from up → down (curling motion completes)
    if (previousStage === 'up' && stage === 'down') {
        if (countRep()) {
            // Update display
            if (typeof statValueDisplay !== 'undefined') {
                statValueDisplay.textContent = repCount;
            }

            // Voice feedback
            speak(repCount);

            // UI feedback
            if (typeof updateFeedback === 'function') {
                updateFeedback('good', 'Great rep! Extend your arm');
            }
        }
    }

    // ==================== UI UPDATES ====================
    // Update status display
    if (typeof statusDisplay !== 'undefined') {
        if (stage === 'down') {
            statusDisplay.textContent = 'Arm Curled (Curl up!)';
        } else if (stage === 'up') {
            statusDisplay.textContent = 'Arm Extended (Extend!)';
        }
    }

    // Draw skeleton
    drawSkeleton(leftShoulder, leftElbow, leftWrist, canvasCtx, canvasElement);
    drawSkeleton(rightShoulder, rightElbow, rightWrist, canvasCtx, canvasElement);

    // Draw angle on screen
    canvasCtx.font = 'bold 24px Inter, sans-serif';
    canvasCtx.fillStyle = '#00ff00';
    canvasCtx.fillText(`${Math.round(currentAngle)}°`, canvasElement.width / 2, 50);

    // Draw stage
    canvasCtx.font = '16px Inter, sans-serif';
    canvasCtx.fillStyle = '#ffffff';
    canvasCtx.fillText(`Stage: ${stage.toUpperCase()}`, 20, canvasElement.height - 20);
}

// ==================== DRAW SKELETON HELPER ====================
function drawSkeleton(shoulder, elbow, wrist, ctx, canvas) {
    ctx.beginPath();
    ctx.moveTo(shoulder.x * canvas.width, shoulder.y * canvas.height);
    ctx.lineTo(elbow.x * canvas.width, elbow.y * canvas.height);
    ctx.lineTo(wrist.x * canvas.width, wrist.y * canvas.height);
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 4;
    ctx.stroke();

    // Draw joints
    [shoulder, elbow, wrist].forEach(point => {
        ctx.beginPath();
        ctx.arc(point.x * canvas.width, point.y * canvas.height, 8, 0, 2 * Math.PI);
        ctx.fillStyle = '#ff6b6b';
        ctx.fill();
    });
}

// ==================== EXPORT FOR USE IN ONRESULTS ====================
// Use this function in your onResults handler:
//
// if (results.poseLandmarks) {
//     detectBicepCup(results.poseLandmarks, canvasCtx, canvasElement);
// }
