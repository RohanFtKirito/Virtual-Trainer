# TODO: Add Voice Feedback to Exercise Modules

## Problem
Voice feedback is not working in exercise files. The `speak()` function only has `pass`.

## Solution
Add pyttsx3 text-to-speech support with platform-independent initialization.

## Implementation Requirements Applied:
1. Import pyttsx3 at top
2. Initialize engine inside main() function (not globally) for better Mac compatibility
3. No `sapi5` (Windows-only)
4. speak() function:
   ```python
   def speak(msg):
       engine.say(str(msg))
       engine.runAndWait()
   ```

## Voice Logic:
- **Rep Counting (BicepCurl, PushUp)**: Speak every rep, no flag logic
- **Posture (Plank, DownwardDog)**: Use flag logic to avoid continuous speech

## Changes Made:
1. **BicepCurl_final.py**: Engine inside main(), debug voice test, speak on rep count
2. **PushUp.py**: Engine inside main(), debug voice test, speak on rep count
3. **Plank.py**: Engine inside main(), debug voice test, flag logic for posture changes
4. **DownwardFacingDog.py**: Engine inside main(), debug voice test, flag logic for posture changes

## Debug Features Added:
- Voice test at exercise start: "Exercise started"
- Console log: "Voice Triggered for Rep: X"
- No repeated engine initialization inside while loop

## Status:
- [x] Fix BicepCurl_final.py
- [x] Fix PushUp.py
- [x] Fix Plank.py
- [x] Fix DownwardFacingDog.py

