// Plank Detection Script
// Variables for plank tracking
let startTime = null;
let elapsedSeconds = 0;
let timerInterval = null;
let formScore = 0;
let isInPlankPosition = false;

// Timer functions
function startTimer() {
    if (!timerInterval) {
        timerInterval = setInterval(() => {
            elapsedSeconds++;
            const mins = Math.floor(elapsedSeconds / 60);
            const secs = elapsedSeconds % 60;
            statValueDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }, 1000);
    }
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

// Format time as MM:SS
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Get key body points for plank form analysis
const landmarks = results.poseLandmarks;

const leftShoulder = landmarks[11];
const rightShoulder = landmarks[12];
const leftHip = landmarks[23];
const rightHip = landmarks[24];
const leftKnee = landmarks[25];
const rightKnee = landmarks[26];
const leftAnkle = landmarks[27];
const rightAnkle = landmarks[28];

// Check visibility
const isVisible = leftShoulder.visibility > 0.5 && rightShoulder.visibility > 0.5 &&
                  leftHip.visibility > 0.5 && rightHip.visibility > 0.5 &&
                  leftAnkle.visibility > 0.5 && rightAnkle.visibility > 0.5;

if (isVisible) {
    // Calculate average positions
    const shoulderY = (leftShoulder.y + rightShoulder.y) / 2;
    const hipY = (leftHip.y + rightHip.y) / 2;
    const ankleY = (leftAnkle.y + rightAnkle.y) / 2;

    // Calculate form score based on body alignment
    // Ideal plank: shoulders, hips, and ankles should be roughly aligned horizontally
    const hipDeviation = Math.abs(hipY - (shoulderY + ankleY) / 2);
    const maxDeviation = 0.15; // Maximum allowed deviation
    const formQuality = Math.max(0, 1 - (hipDeviation / maxDeviation));
    formScore = Math.round(formQuality * 100);

    // Update form score display (reuse statValueDisplay for score)
    document.getElementById('formScore').textContent = formScore + '%';

    // Determine if in proper plank position
    if (formScore >= 70) {
        if (!isInPlankPosition) {
            isInPlankPosition = true;
            startTime = Date.now();
            startTimer();
            statusDisplay.textContent = 'Holding...';
            updateFeedback('good', 'Great form! Keep holding');
        }
    } else {
        if (isInPlankPosition) {
            isInPlankPosition = false;
            stopTimer();
            statusDisplay.textContent = 'Adjust Position';
        }
        updateFeedback('warning', `Form score: ${formScore}% - Adjust your position`);
    }

    // Draw body line for visual feedback
    canvasCtx.beginPath();
    canvasCtx.moveTo((leftShoulder.x + rightShoulder.x) / 2 * canvasElement.width,
                   shoulderY * canvasElement.height);
    canvasCtx.lineTo((leftHip.x + rightHip.x) / 2 * canvasElement.width,
                   hipY * canvasElement.height);
    canvasCtx.lineTo((leftAnkle.x + rightAnkle.x) / 2 * canvasElement.width,
                   ankleY * canvasElement.height);
    canvasCtx.strokeStyle = formScore >= 70 ? '#28a745' : '#ffc107';
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();

} else {
    updateFeedback('warning', 'Move into frame');
    statusDisplay.textContent = 'Not Detected';
}
