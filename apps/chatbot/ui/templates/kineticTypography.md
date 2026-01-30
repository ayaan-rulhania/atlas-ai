# Kinetic Typography

A hover-triggered 3D animation effect that makes individual characters in a title pop forward with a staggered animation.

## JavaScript/React Implementation

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

## CSS Implementation

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

## How to Implement

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
