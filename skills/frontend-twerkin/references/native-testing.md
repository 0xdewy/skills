# Native Testing Guide (Expo / React Native)

Read this file when `detect_stack.sh` reports `IS_NATIVE=true`. Native apps require different tooling and attack vectors than web apps. This guide covers Detox for E2E testing and mobile-specific adversarial attacks.

---

## 1. Tooling Setup

### Detox (for React Native / Expo)

Detox is the standard E2E framework for React Native. Set it up if not already present:

```bash
# Check if Detox is installed
if ! grep -q '"detox"' package.json; then
  # Install Detox
  npm install -D detox detox-cli
  # Or: pnpm add -D detox detox-cli

  # Initialize Detox config
  npx detox init -r jest
fi
```

### Expo Web Mode (bridge strategy)

If Playwright is needed for visual checks and the Expo app supports web:
```bash
npx expo start --web
# Then point Playwright at the Expo web URL (usually localhost:8081)
```

This allows using Playwright's screenshot and visual comparison tools even for native apps, though it only tests the web renderer — not native behavior.

### iOS Simulator
```bash
# Check for available simulators
xcrun simctl list devices available | grep -i iphone
# Boot a simulator
xcrun simctl boot "iPhone 15"
```

### Android Emulator
```bash
# List available AVDs
emulator -list-avds
# Start an emulator
emulator -avd Pixel_8_API_34 &
```

---

## 2. Mobile-Specific Adversarial Attacks

### 2.1 Device rotation
**What:** Rotate the device mid-interaction (portrait ↔ landscape).
**Detox approach:**
```js
await device.setOrientation('landscape');
await expect(element(by.text('Some Content'))).toBeVisible();
await device.setOrientation('portrait');
```
**Look for:** Layout breaks in landscape, text overflow, modals that don't reorient, images that don't resize, scroll position reset.

### 2.2 Background/foreground cycling
**What:** Send the app to background and bring it back rapidly.
**Detox approach:**
```js
await device.sendToHome();
await device.launchApp({ newInstance: false });
// Repeat 5x rapidly
```
**Look for:** State lost on resume, blank screen, re-authentication triggered unnecessarily, pending network requests not retried, crash on resume.

### 2.3 Low memory warning simulation
**What:** Simulate iOS low-memory conditions.
**iOS Simulator:**
```bash
xcrun simctl spawn booted simulate_memory_warning
```
**Look for:** App evicted from memory and doesn't restore state, images/media reloaded from network (not cached), crash.

### 2.4 Touch gesture stress
**What:** Perform rapid taps, swipes, and pinches in quick succession.
**Detox approach:**
```js
await element(by.id('scroll-view')).swipe('up', 'fast');
await element(by.id('scroll-view')).swipe('down', 'fast');
await element(by.id('button')).multiTap(5);
```
**Look for:** Gesture recognizer conflicts, scroll position jumping, buttons responding to every tap (should they debounce?), list items reordering on rapid swipe.

### 2.5 Keyboard interactions
**What:** Show/hide keyboard while scrolling, rotating, and navigating.
**Detox approach:**
```js
await element(by.id('text-input')).tap(); // keyboard shows
await device.setOrientation('landscape'); // rotate with keyboard open
await element(by.id('scroll-view')).swipe('up'); // scroll with keyboard
```
**Look for:** Keyboard overlaps input being typed into, layout doesn't adjust for keyboard, scroll view doesn't scroll to focused input, keyboard stays open when navigating away.

### 2.6 Deep link injection
**What:** Open the app via deep link with malformed or unexpected URLs.
```bash
xcrun simctl openurl booted "myapp://deeplink/../../sensitive-screen"
xcrun simctl openurl booted "myapp://deeplink/<script>alert(1)</script>"
```
**Look for:** Unauthorized screen access, crash on malformed URL, XSS in any WebView that renders the URL.

### 2.7 Permission flow
**What:** Deny all permissions, then attempt to use features requiring them. Then grant mid-flow.
**Look for:** App doesn't explain why permission needed, crash on permission denial, stuck in limbo after denying (no retry path), permission prompt spammed on every launch.

---

## 3. Platform-Specific Checks

### iOS
- **Safe area:** Content doesn't overlap notch or home indicator on iPhone X+
- **Dynamic type:** Enable largest accessibility text size and check layout
- **Swipe back gesture:** Navigation doesn't break with iOS back-swipe
- **Control Center swipe:** Pull down control center mid-interaction, dismiss, check state

### Android
- **System back button:** Android back behavior is correct (not just in-app back)
- **Split screen:** Enter split-screen mode and check layout
- **Notification shade:** Pull down notification shade and check app state on dismiss
- **Bottom sheet navigation:** Android gesture navigation doesn't conflict with app gestures

---

## 4. Performance Checks

### Animation frame rate
Use Flipper or React DevTools Profiler to check:
- Smooth 60fps during list scrolling
- No frame drops during screen transitions
- Animation doesn't stutter when network requests are in flight

### Memory leaks
- Navigate through 10+ screens, then back to start
- Check memory usage hasn't grown significantly
- Repeat navigation cycle 5 times — linear growth = leak

### Cold start time
```bash
# iOS
xcrun simctl launch --console-pty booted com.app.bundleid 2>&1 | head -50
```
Flag if initial render takes >2 seconds on a modern device.
