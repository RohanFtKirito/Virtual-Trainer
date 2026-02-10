# TODO: Add Voice Feedback to Flask Browser-Based App

## Problem
The Flask app uses JavaScript-based MediaPipe detection (not Python). 
Standalone Python scripts won't trigger voice in browser.

## Solution
Add JavaScript Web Speech API for browser-based voice feedback.

## Implementation:
```javascript
// Initialize speech synthesis
const synth = window.speechSynthesis;

function speak(text) {
    if (synth.speaking) return; // Prevent overlapping
    const utterance = new SpeechSynthesisUtterance(String(text));
    utterance.rate = 1.2;
    synth.speak(utterance);
}
```

## Files Updated:
1. **exercise-bicepcurl.html** - Speak rep count when rep completes
2. **exercise-pushup.html** - Speak rep count when rep completes
3. **exercise-downwarddog.html** - Speak posture changes with flag logic

## Voice Logic:
- **Rep Counting (BicepCurl, PushUp)**: Speak count on each rep completion
- **Posture (DownwardDog)**: Speak when status changes using flag to avoid repetition

## Changes Made:
1. Added `synth` (speech synthesis) initialization
2. Added `speak()` function with overlap protection
3. Added debug voice test: "Exercise started" on page load
4. Added speak() calls at appropriate detection points

## Status:
- [x] Update exercise-bicepcurl.html
- [x] Update exercise-pushup.html
- [x] Update exercise-downwarddog.html
- [x] exercise-plank.html (already had JavaJS logic)

