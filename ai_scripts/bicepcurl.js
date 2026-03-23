// Bicep Curl Detection Script
// Variables for rep counting
let repCount = 0;
let stage = 'up'; // 'up' = arm extended, 'down' = arm curled

// Initialize speech synthesis for voice feedback
const synth = window.speechSynthesis;

function speak(text) {
    if (synth.speaking) return;
    const utterance = new SpeechSynthesisUtterance(String(text));
    utterance.rate = 1.2;
    utterance.pitch = 1.0;
    synth.speak(utterance);
}

// Test voice on page load
setTimeout(() => {
    speak("Exercise started");
}, 1000);

// Get relevant landmarks for bicep curl
const landmarks = results.poseLandmarks;

// Left arm landmarks (assuming person is facing camera)
const leftShoulder = landmarks[11];
const leftElbow = landmarks[13];
const leftWrist = landmarks[15];
const rightShoulder = landmarks[12];
const rightElbow = landmarks[14];
const rightWrist = landmarks[16];

// Check if person is visible
const isVisible = leftShoulder.visibility > 0.5 && leftElbow.visibility > 0.5 && leftWrist.visibility > 0.5;

if (isVisible) {
    // Calculate angle for both arms
    const leftAngle = calculateAngle(leftShoulder, leftElbow, leftWrist);
    const rightAngle = calculateAngle(rightShoulder, rightElbow, rightWrist);
    const avgAngle = (leftAngle + rightAngle) / 2;

    // Update stage based on angle
    if (avgAngle > 160) {
        stage = 'up';
        statusDisplay.textContent = 'Arm Extended';
        updateFeedback('good', 'Extend your arm');
    } else if (avgAngle < 40 && stage === 'up') {
        stage = 'down';
        repCount++;
        statValueDisplay.textContent = repCount;
        statusDisplay.textContent = 'Arm Curled ✓';
        updateFeedback('good', 'Good rep! Extend your arm');
        // Voice feedback for rep count
        speak(repCount);
    } else if (avgAngle < 160 && avgAngle > 40) {
        statusDisplay.textContent = 'Moving...';
    }

    // Draw arm lines
    canvasCtx.beginPath();
    canvasCtx.moveTo(leftShoulder.x * canvasElement.width, leftShoulder.y * canvasElement.height);
    canvasCtx.lineTo(leftElbow.x * canvasElement.width, leftElbow.y * canvasElement.height);
    canvasCtx.lineTo(leftWrist.x * canvasElement.width, leftWrist.y * canvasElement.height);
    canvasCtx.strokeStyle = '#28a745';
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();

    canvasCtx.beginPath();
    canvasCtx.moveTo(rightShoulder.x * canvasElement.width, rightShoulder.y * canvasElement.height);
    canvasCtx.lineTo(rightElbow.x * canvasElement.width, rightElbow.y * canvasElement.height);
    canvasCtx.lineTo(rightWrist.x * canvasElement.width, rightWrist.y * canvasElement.height);
    canvasCtx.stroke();

    // Draw angle text
    canvasCtx.font = 'bold 24px Inter, sans-serif';
    canvasCtx.fillStyle = 'white';
    canvasCtx.fillText(`${Math.round(avgAngle)}°`, canvasElement.width / 2, 50);
} else {
    updateFeedback('warning', 'Move into frame');
    statusDisplay.textContent = 'Not Detected';
}
