# Design system: Arterion Coronary Dominance

A recreation of a clean medical-AI landing page, in emerald green and white. Every claim and number on the page comes from this project's own README and metrics.

## Structure
1. Floating navigation: logo mark, pill tabs, status, sign-in, Get Started
2. Hero: badge, serif headline (italic gradient second line), lead, two calls to action, check-badges, motif line
3. Features: six cards with gradient icon tiles
4. Process: four numbered steps joined by a rail that fills as you scroll
5. Analyze: the working tool
6. Evidence: dark section with an italic claim and a glass panel of held-out metric bars
7. Call to action and footer

## Tokens
| Token | Value |
|---|---|
| `--brand-1` | `#14532d` |
| `--brand-2` | `#15803d` |
| `--brand-3` | `#22c55e` |
| `--bright` | `#86efac` |
| `--ink` | `#0d2418` |
| `--muted` | `#5b7566` |
| `--bg` | `#f7fdf9` |
| `--soft` | `#f0fdf4` |
| `--dark-1` | `#06261a` |
| `--dark-2` | `#14532d` |

## Type
Headlines: 'Libre Baskerville'. Body: 'DM Sans'. Numbers: 'Spline Sans Mono'.

## Motion
- **Motion (framer-motion engine, vanilla build):** hero entrance on a spring, button hover and press springs, count-ups.
- **GSAP + ScrollTrigger:** read-progress bar, hero parallax, heading and card reveals, a scrubbed rail that connects the steps, metric bars that grow once in view.
- **Reduced motion:** all animation is skipped and bars and counters show their final values.

## Accessibility
Skip link, labelled landmarks, visible focus rings, text contrast of at least 4.5:1 on buttons, and a keyboard-operable mobile menu.
