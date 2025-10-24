# Real's Mobile Inventory - Color Palette

## Gradient Background
```css
background: linear-gradient(
  to bottom,
  #FFE8B6 10%,   /* Light Peach/Cream */
  #AED09E 50%,   /* Light Green/Sage */
  #77B254 100%   /* Medium Green/Olive - Main Brand Color */
);
```

## Primary Colors
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Light Peach | `#FFE8B6` | Gradient top (10%) |
| Light Sage Green | `#AED09E` | Gradient middle (50%) |
| Olive Green | `#77B254` | Gradient bottom, Primary brand color, Buttons |
| Dark Olive | `#5d8f42` | Button hover state |

## Text Colors
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Dark Slate | `#2f3e46` | Headings, primary text |
| Medium Gray | `#555555` | Secondary text, descriptions |
| White | `#ffffff` | Navbar text, button text |

## Glass/Transparency Effects
| Effect | RGBA Value | Usage |
|--------|------------|-------|
| Card Background | `rgba(255, 255, 255, 0.7)` | Dashboard cards |
| Login Card | `rgba(255, 255, 255, 0.6)` | Login form background |
| Navbar | `rgba(0, 0, 0, 0.4)` | Navigation bar |
| Button Base | `rgba(255, 255, 255, 0.2)` | iOS-style buttons |
| Button Hover | `rgba(255, 255, 255, 0.35)` | Button hover effect |

## Status Colors
| Status | Hex/RGBA | Usage |
|--------|----------|-------|
| Offline Warning | `#ff9800` | Orange - No internet indicator |
| Online Status | `#90EE90` | Light green - Connected indicator |

## Design Specifications
- **Border Radius**: 12px (buttons), 18px (cards), 20px (login card)
- **Backdrop Blur**: 12px (navbar), 15px (cards)
- **Font Family**: 'Poppins', sans-serif
- **Shadow**: `0 4px 12px rgba(0,0,0,0.08)` (cards)
- **Hover Shadow**: `0 8px 20px rgba(0,0,0,0.15)` (cards on hover)

## CSS Variables (Optional - for easy implementation)
```css
:root {
  /* Primary Colors */
  --color-peach: #FFE8B6;
  --color-sage: #AED09E;
  --color-olive: #77B254;
  --color-olive-dark: #5d8f42;
  
  /* Text Colors */
  --color-text-primary: #2f3e46;
  --color-text-secondary: #555555;
  --color-text-light: #ffffff;
  
  /* Status Colors */
  --color-offline: #ff9800;
  --color-online: #90EE90;
  
  /* Glass Effects */
  --glass-card: rgba(255, 255, 255, 0.7);
  --glass-login: rgba(255, 255, 255, 0.6);
  --glass-navbar: rgba(0, 0, 0, 0.4);
  --glass-button: rgba(255, 255, 255, 0.2);
  --glass-button-hover: rgba(255, 255, 255, 0.35);
  
  /* Design Specs */
  --radius-button: 12px;
  --radius-card: 18px;
  --radius-login: 20px;
  --blur-navbar: 12px;
  --blur-card: 15px;
}
```

## Tailwind CSS Equivalent (if using Tailwind)
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'reals-peach': '#FFE8B6',
        'reals-sage': '#AED09E',
        'reals-olive': '#77B254',
        'reals-olive-dark': '#5d8f42',
        'reals-slate': '#2f3e46',
        'reals-gray': '#555555',
        'reals-offline': '#ff9800',
        'reals-online': '#90EE90',
      },
      backdropBlur: {
        'reals': '15px',
      },
      borderRadius: {
        'reals-button': '12px',
        'reals-card': '18px',
        'reals-login': '20px',
      }
    }
  }
}
```

## Design Style
- **Theme**: Glassmorphism with gradient background
- **Inspiration**: iOS/Apple design language
- **Key Features**: 
  - Smooth transitions (0.25s - 0.3s ease)
  - Backdrop blur effects
  - Subtle shadows and hover effects
  - Clean, modern, minimalist aesthetic
