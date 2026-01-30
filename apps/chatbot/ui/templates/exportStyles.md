# Export Styles Documentation

This document contains reusable style implementations from the Arcade project, including kinetic typography, glassmorphic card designs, and animated backgrounds.

---

## 1. Kinetic Typography

A hover-triggered 3D animation effect that makes individual characters in a title pop forward with a staggered animation.

### JavaScript/React Implementation

```jsx
import React, { useEffect, useRef } from 'react'

function ComponentWithKineticTypography() {
  const titleRef = useRef(null)

  useEffect(() => {
    const titleEl = titleRef.current
    if (!titleEl) return

    const text = titleEl.textContent
    titleEl.innerHTML = '' // clear before injecting spans

    // Split text into individual character spans
    ;[...text].forEach((ch, i) => {
      const span = document.createElement('span')
      span.className = 'char'
      span.style.display = 'inline-block'
      span.style.animationDelay = `${i * 40}ms, ${i * 60}ms`
      span.textContent = ch === ' ' ? '\u00A0' : ch // preserve spaces with non-breaking space
      titleEl.appendChild(span)
    })

    // Hover kinetic pop animation
    titleEl.addEventListener('mouseenter', () => {
      ;[...titleEl.querySelectorAll('.char')].forEach((el, idx) => {
        el.animate(
          [
            { transform: 'translateZ(0) scale(1)' },
            { transform: 'translateZ(24px) scale(1.08)' },
            { transform: 'translateZ(0) scale(1)' },
          ],
          {
            duration: 480,
            delay: idx * 18,
            easing: 'cubic-bezier(.2,.9,.2,1)',
          }
        )
      })
    })
  }, [])

  return (
    <h1 ref={titleRef} className="menu-title">
      Your Title Here
    </h1>
  )
}
```

### CSS Implementation

```css
.menu-title {
  font-size: clamp(36px, 8vw, 48px);
  font-weight: 900;
  letter-spacing: -1px;
  line-height: 0.95;
  margin: 4px 0 12px;
  display: inline-block;
  transform-style: preserve-3d;
  perspective: 800px;
}

.menu-title .char {
  display: inline-block;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  background-image: linear-gradient(
    90deg,
    #8fb0ff 0%,
    #b27bff 18%,
    #ff6fb1 36%,
    #ff8f6a 56%,
    #ffd77a 72%,
    #a8d9ff 100%
  );
  background-size: 240% 240%;
  animation: gradientFlow 6s ease-in-out infinite, floatTilt 4s ease-in-out infinite;
  transform-origin: center;
  will-change: transform;
  text-shadow: 0 6px 24px rgba(130, 90, 220, 0.12);
  margin-right: 1px;
}

@keyframes gradientFlow {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

@keyframes floatTilt {
  0% {
    transform: translateZ(0px) rotateX(0deg);
  }
  25% {
    transform: translateZ(4px) rotateX(1deg);
  }
  50% {
    transform: translateZ(0px) rotateX(0deg);
  }
  75% {
    transform: translateZ(-2px) rotateX(-0.6deg);
  }
  100% {
    transform: translateZ(0px) rotateX(0deg);
  }
}

.menu-title:hover .char {
  animation-duration: 4s, 2.6s;
  transform-origin: center;
}
```

### How to Implement

1. **Add the React hook** to your component:
   - Import `useRef` and `useEffect` from React
   - Create a ref using `useRef(null)`
   - Attach the ref to your title element

2. **Add the JavaScript logic**:
   - In a `useEffect` hook, get the title element using the ref
   - Split the text content into individual characters
   - Wrap each character in a `<span>` with class `char`
   - Add a `mouseenter` event listener that triggers the animation

3. **Add the CSS**:
   - Copy the `.menu-title` and `.menu-title .char` styles
   - Copy the `@keyframes gradientFlow` and `@keyframes floatTilt` animations
   - Adjust colors, sizes, and timing to match your design

4. **Customization**:
   - Change the gradient colors in `.char` background-image
   - Adjust animation duration (currently 480ms)
   - Modify the delay multiplier (currently `idx * 18`)
   - Change the scale and translateZ values for different pop intensity

---

## 2. Glassmorphic Card Design

A modern card design with glassmorphism effects, smooth hover animations, and gradient text. Includes styling for cards, card headers, card descriptions, and section subtitles.

### CSS Implementation

#### Card Container Styles

```css
.game-card {
  border: none;
  border-radius: 24px;
  padding: 28px 24px;
  cursor: pointer;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
  background: rgba(8, 12, 22, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  color: inherit;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.game-card:focus-visible {
  outline: 2px solid #38f9d7;
  outline-offset: 4px;
}

.game-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.45);
}
```

#### Card Text Styles

```css
/* Card Header/Title - Animated Gradient Text */
.game-name {
  font-size: 1.8rem;
  font-weight: 600;
  background: linear-gradient(120deg, #43e97b, #38f9d7, #667eea, #764ba2);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: gradientFlow 8s ease infinite;
}

/* Card Description/Body Text */
.game-description {
  font-size: 0.95rem;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.8);
}
```

#### Section Subtitle (Above Cards)

```css
/* Subtitle text that appears above the card grid */
.menu-subtitle {
  font-size: 1.25rem;
  margin-bottom: 20px;
  color: rgba(255, 255, 255, 0.75);
}
```

#### Gradient Flow Animation (Required for Card Headers)

```css
@keyframes gradientFlow {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
```

#### Responsive Text Sizes

```css
/* Tablet (max-width: 768px) */
@media (max-width: 768px) {
  .menu-subtitle {
    font-size: 1.1rem;
    margin-bottom: 18px;
  }

  .game-name {
    font-size: 1.6rem;
  }

  .game-description {
    font-size: 0.9rem;
  }
}

/* Mobile (max-width: 480px) */
@media (max-width: 480px) {
  .menu-subtitle {
    font-size: 1rem;
    margin-bottom: 15px;
    padding: 0 10px;
  }

  .game-name {
    font-size: 1.4rem;
  }

  .game-description {
    font-size: 0.85rem;
  }
}
```

### HTML/JSX Structure

```jsx
<div className="menu-container">
  <h1 className="menu-title">Main Title</h1>
  <p className="menu-subtitle">Choose a game to play</p>
  
  <div className="games-grid">
    <button className="game-card" type="button">
      <h2 className="game-name">Card Title</h2>
      <p className="game-description">Card description text here</p>
    </button>
  </div>
</div>
```

### How to Implement

1. **Add the base card styles**:
   - Copy `.game-card` styles to your CSS file
   - The key properties are:
     - `background: rgba(8, 12, 22, 0.75)` - semi-transparent background
     - `backdrop-filter: blur(20px)` - creates the glass effect
     - `border: 1px solid rgba(255, 255, 255, 0.08)` - subtle border

2. **Add hover effects**:
   - The `.game-card:hover` rule creates the lift effect
   - Adjust `translateY(-8px)` to change lift distance
   - Modify `box-shadow` for different shadow intensity

3. **Add card text styles**:
   - **Card Headers (`.game-name`)**: Animated gradient text effect
     - Requires the `gradientFlow` keyframe animation
     - Uses `background-clip: text` to create gradient text
     - Adjust gradient colors to match your theme
   - **Card Descriptions (`.game-description`)**: Regular body text
     - Semi-transparent white color for readability
     - Adjust `font-size` and `line-height` as needed

4. **Add section subtitle**:
   - Use `.menu-subtitle` for text that appears above the card grid
   - Semi-transparent white color for subtle appearance
   - Adjust `margin-bottom` for spacing

5. **Customization**:
   - **Card styling**: Change `border-radius`, `padding`, `backdrop-filter: blur()` value
   - **Card header colors**: Update gradient colors in `.game-name` (currently: `#43e97b, #38f9d7, #667eea, #764ba2`)
   - **Card description color**: Change `color` value in `.game-description` (currently `rgba(255, 255, 255, 0.8)`)
   - **Subtitle color**: Adjust `color` in `.menu-subtitle` (currently `rgba(255, 255, 255, 0.75)`)
   - **Font sizes**: Adjust `font-size` values for different text scales
   - **Animation speed**: Change `8s` in `.game-name` animation for faster/slower gradient flow

---

## 3. Animated Background

A multi-layer animated gradient background that creates a dynamic, flowing color effect.

### CSS Implementation

```css
body {
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  color: var(--text-primary);
  background: radial-gradient(circle at 20% 20%, rgba(72, 149, 239, 0.25), transparent 50%),
              radial-gradient(circle at 80% 0%, rgba(252, 92, 125, 0.18), transparent 50%),
              radial-gradient(circle at 50% 80%, rgba(102, 126, 234, 0.15), transparent 45%),
              linear-gradient(135deg, #030508, #05070f 35%, #0a0e18 70%, #030508);
  background-size: 300% 300%;
  animation: gradientFlow 20s ease infinite;
}

@keyframes gradientFlow {
  0% {
    background-position: 0% 0%, 100% 100%, 50% 50%, 0% 50%;
  }
  33% {
    background-position: 100% 50%, 0% 0%, 100% 100%, 50% 100%;
  }
  66% {
    background-position: 50% 100%, 50% 50%, 0% 0%, 100% 50%;
  }
  100% {
    background-position: 0% 0%, 100% 100%, 50% 50%, 0% 50%;
  }
}
```

### How to Implement

1. **Apply to body or container**:
   - Add the background styles to your `body` element or any container
   - The background uses multiple layered gradients:
     - Three radial gradients for colored orbs
     - One linear gradient as the base

2. **Structure the gradients**:
   - Each gradient is separated by commas
   - They stack on top of each other (first = top layer)
   - Use `transparent` to allow lower layers to show through

3. **Set background-size**:
   - `background-size: 300% 300%` makes the gradients larger than the viewport
   - This allows them to move around during animation

4. **Add the animation**:
   - The `gradientFlow` keyframe animates `background-position`
   - Each percentage in the keyframe corresponds to one gradient layer
   - Adjust the duration (20s) for faster/slower animation

5. **Customization**:
   - **Change colors**: Modify the rgba values in radial gradients
   - **Change positions**: Adjust `circle at X% Y%` values
   - **Add more layers**: Add more radial-gradient() entries
   - **Animation speed**: Change `20s` to desired duration
   - **Animation style**: Change `ease` to `linear`, `ease-in-out`, etc.
   - **Base gradient**: Modify the linear-gradient colors for different base tones

### Example: Simplified Version

```css
/* Simpler version with just two gradients */
body {
  background: radial-gradient(circle at 30% 30%, rgba(72, 149, 239, 0.3), transparent 50%),
              linear-gradient(135deg, #030508, #0a0e18);
  background-size: 200% 200%;
  animation: simpleFlow 15s ease infinite;
}

@keyframes simpleFlow {
  0%, 100% {
    background-position: 0% 0%, 0% 0%;
  }
  50% {
    background-position: 100% 100%, 0% 0%;
  }
}
```

---

## Usage Notes

- **Browser Support**: All styles use modern CSS features. Ensure your target browsers support:
  - `backdrop-filter` (for glassmorphism)
  - CSS animations
  - CSS gradients
  - `transform-style: preserve-3d` (for kinetic typography)

- **Performance**: 
  - The kinetic typography uses `will-change: transform` for optimization
  - Background animation is GPU-accelerated
  - Card hover effects use CSS transitions for smooth performance

- **Accessibility**:
  - Cards include `:focus-visible` styles for keyboard navigation
  - Ensure sufficient color contrast for text readability
  - Consider `prefers-reduced-motion` media query for users who prefer less animation

---

## License

These styles are part of the Arcade project. Feel free to use and modify as needed.
