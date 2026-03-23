// Push-Up Detection Script
// Variables for rep counting
let repCount = 0;
let stage = 'up'; // 'up' = body up, 'down' = body down

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

// Get landmarks for push-up detection
const landmarks = results.poseLandmarks;

// Get landmarks for push-up detection
const leftShoulder = landmarks[11];
const rightShoulder = landmarks[12];
const leftElbow = landmarks[13];
const rightElbow = landmarks[14];
const leftWrist = landmarks[15];
const rightWrist = landmarks[16];

// Check visibility
const isVisible = leftShoulder.visibility > 0.5 && rightShoulder.visibility > 0.5 &&
                  leftWrist.visibility > 0.5 && rightWrist.visibility > 0.5;

if (isVisible) {
    // Calculate body angle (shoulder-hip-wrist approximation)
    const leftAngle = calculateAngle(leftShoulder, {x: (leftShoulder.x + leftWrist.x) / 2, y: leftShoulder.y}, leftWrist);
    const rightAngle = calculateAngle(rightShoulder, {x: (rightShoulder.x + rightWrist.x) / 2, y: rightShoulder.y}, rightWrist);
    const avgAngle = (leftAngle + rightAngle) / 2;

    // Update stage based on body angle
    if (avgAngle > 160) {
        stage = 'up';
        statusDisplay.textContent = 'Body Up';
        updateFeedback('good', 'Lower your body');
    } else if (avgAngle < 70 && stage === 'up') {
        stage = 'down';
        repCount++;
        statValueDisplay.textContent = repCount;
        statusDisplay.textContent = 'Body Down ✓';
        updateFeedback('good', 'Good rep! Push up');
        speak(repCount);
    } else if (avgAngle < 160 && avgAngle > 70) {
        statusDisplay.textContent = 'Moving...';
    }

    // Draw body lines
    canvasCtx.beginPath();
    canvasCtx.moveTo(leftShoulder.x * canvasElement.width, leftShoulder.y * canvasElement.height);
    canvasCtx.lineTo(leftWrist.x * canvasElement.width, leftWrist.y * canvasElement.height);
    canvasCtx.strokeStyle = '#28a745';
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();

    canvasCtx.beginPath();
    canvasCtx.moveTo(rightShoulder.x * canvasElement.width, rightShoulder.y * canvasElement.height);
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
