# UI Branding Implementation Guide

**Target UIs:** InvestmAit Frontend, FedSuite Frontend
**Date:** 2025-10-06

---

## Status Summary

### ✅ cortx-designer Frontend

**Status:** COMPLETE - Already branded with Sinergy colors, fonts, and accessibility features

### ⚠️ InvestmAit Frontend

**Location:** `corpsuite/modules/investmait/frontend`
**Needs:** Sinergy colors, fonts, Radix UI components, dark mode

### ⚠️ FedSuite Frontend

**Location:** `fedsuite/frontend`
**Needs:** Sinergy colors (Federal Navy accent), fonts, Radix UI, dark mode, Recharts

---

## Branding Implementation Steps

### Step 1: Update Tailwind Config

Add Sinergy brand colors and fonts to `tailwind.config.js`:

```javascript
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        'heading': ['Space Grotesk', 'sans-serif'],
        'subtitle': ['DM Sans', 'sans-serif'],
        'subheading': ['Manrope', 'sans-serif'],
        'section': ['Sora', 'sans-serif'],
        'body': ['IBM Plex Sans', 'sans-serif'],
        'quote': ['Lora', 'serif'],
        'caption': ['Roboto', 'sans-serif'],
        'sans': ['IBM Plex Sans', 'sans-serif'],
      },
      colors: {
        // Sinergy Solutions brand colors
        "sinergy-teal": "#00C2CB",
        "sinergy-navy": "#2D5972",
        "sinergy-clarity-blue": "#E5FCFF",
        "sinergy-slate-gray": "#8CAABF",
        sinergy: {
          teal: "#00C2CB",
          navy: "#2D5972",
          "clarity-blue": "#E5FCFF",
          "slate-gray": "#8CAABF",
        },
        // Extended Sinergy palette
        "navy": {
          50: "#f0f5f9",
          100: "#e0eaf2",
          200: "#c8dae6",
          300: "#a7c3d7",
          400: "#83a8c3",
          500: "#698eab",
          600: "#557490",
          700: "#455e76",
          800: "#394d60",
          900: "#2d5972",
          950: "#1f3443",
        },
        "teal": {
          50: "#f0fcfc",
          100: "#cffafa",
          200: "#a9f5f6",
          300: "#72edef",
          400: "#34e1e6",
          500: "#00c2cb",
          600: "#00a0a8",
          700: "#008187",
          800: "#00666b",
          900: "#005459",
          950: "#003538",
        },
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
}
```

### Step 2: Update globals.css

Add font imports and Sinergy CSS variables:

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;600&family=Manrope:wght@400;500;600;700&family=Sora:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Lora:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Sinergy Solutions Brand Colors */
    --sinergy-teal: #00C2CB;
    --federal-navy: #2D5972;
    --clarity-blue: #E5FCFF;
    --slate-gray: #8CAABF;

    /* Light mode theme */
    --background: 0 0% 100%;
    --foreground: 207 29% 15%;
    --primary: 183 100% 40%; /* Sinergy Teal */
    --primary-foreground: 207 29% 15%;
    --secondary: 207 29% 35%; /* Federal Navy */
    --secondary-foreground: 0 0% 100%;
    --accent: 183 100% 40%;
    --accent-foreground: 0 0% 100%;
  }

  .dark {
    /* Dark mode theme */
    --background: 210 45% 8%;
    --foreground: 0 0% 100%;
    --primary: 183 100% 40%;
    --primary-foreground: 207 29% 15%;
    --secondary: 207 29% 35%;
    --secondary-foreground: 0 0% 100%;
  }
}

@layer base {
  body {
    @apply bg-background text-foreground;
    font-family: 'IBM Plex Sans', sans-serif;
  }
}
```

### Step 3: Add Sinergy Logos

Copy `SS_Logo_Transparent.png` and `SS-Icon-Transparent.png` to `public/` folder

### Step 4: Install Required Dependencies

#### For InvestmAit

```bash
cd corpsuite/modules/investmait/frontend
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-tooltip @radix-ui/react-icons lucide-react class-variance-authority clsx tailwind-merge
npm install @tailwindcss/forms @tailwindcss/typography
```

#### For FedSuite

```bash
cd fedsuite/frontend
npm install recharts @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-tooltip @radix-ui/react-icons class-variance-authority clsx tailwind-merge
npm install @tailwindcss/forms @tailwindcss/typography
```

### Step 5: Create Shared UI Components

Extract common components to reusable library (future task - Phase 2)

---

## Component Styling Guide

### Buttons

```tsx
// Primary (Sinergy Teal)
<button className="bg-sinergy-teal hover:bg-teal-600 text-white font-subtitle px-4 py-2 rounded-lg transition-colors">
  Submit
</button>

// Secondary (Federal Navy)
<button className="bg-sinergy-navy hover:bg-navy-700 text-white font-subtitle px-4 py-2 rounded-lg transition-colors">
  Cancel
</button>

// Ghost
<button className="border-2 border-sinergy-teal text-sinergy-teal hover:bg-sinergy-teal hover:text-white font-subtitle px-4 py-2 rounded-lg transition-colors">
  Learn More
</button>
```

### Headings

```tsx
<h1 className="font-heading text-4xl font-bold text-sinergy-navy dark:text-white">
  Investment Analysis
</h1>

<h2 className="font-heading text-3xl font-semibold text-navy-800 dark:text-white">
  Scenario Comparison
</h2>

<h3 className="font-subheading text-xl font-medium text-navy-700 dark:text-navy-200">
  Property Details
</h3>
```

### Forms

```tsx
<label className="font-caption text-sm font-medium text-navy-700 dark:text-navy-300">
  Property Address
</label>
<input
  type="text"
  className="border-2 border-sinergy-slate-gray focus:border-sinergy-teal focus:ring-2 focus:ring-sinergy-teal/20 rounded-lg px-3 py-2 font-body"
/>
```

### Charts (Recharts)

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<LineChart data={data}>
  <Line type="monotone" dataKey="value" stroke="#00C2CB" strokeWidth={2} />
  <Line type="monotone" dataKey="forecast" stroke="#2D5972" strokeWidth={2} strokeDasharray="5 5" />
</LineChart>
```

---

## Accessibility Checklist

### WCAG AA Compliance

- [ ] All text has 4.5:1 contrast ratio (use WebAIM contrast checker)
- [ ] Interactive elements have visible focus indicators
- [ ] All images have alt text
- [ ] Forms have proper labels and error messages
- [ ] Keyboard navigation works (Tab, Enter, Escape)

### Screen Reader Support

```tsx
// Add sr-only class for screen reader text
<span className="sr-only">Loading data...</span>

// Use ARIA labels
<button aria-label="Close modal">
  <XIcon />
</button>
```

### Reduced Motion

```css
/* Add to globals.css */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Dark Mode Implementation

### Add Dark Mode Toggle

```tsx
'use client';

import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-lg border-2 border-sinergy-slate-gray hover:border-sinergy-teal transition-colors"
      aria-label="Toggle dark mode"
    >
      {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}
```

### Wrap App in Theme Provider

```tsx
// app/layout.tsx (or _app.tsx for Pages Router)
import { ThemeProvider } from 'next-themes';

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

---

## Testing Checklist

### Visual Regression

- [ ] Compare before/after screenshots
- [ ] Test light mode
- [ ] Test dark mode
- [ ] Test on mobile (375px width)
- [ ] Test on tablet (768px width)
- [ ] Test on desktop (1920px width)

### Functional Testing

- [ ] All buttons clickable
- [ ] Forms submit correctly
- [ ] Charts render data
- [ ] Navigation works
- [ ] Dark mode toggle works

### Performance

- [ ] Lighthouse score 90+ (performance)
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Bundle size < 500KB (gzipped)

---

## Next Steps

1. **Apply branding** to InvestmAit and FedSuite (automated in next commit)
2. **Install dependencies** (Radix UI, Recharts, etc.)
3. **Copy Sinergy logos** to public folders
4. **Test** light/dark modes
5. **Run Lighthouse audits**
6. **Extract shared components** to `packages/cortx-ui` (Phase 2)

---

## Resources

- [Sinergy Brand Guide](/UI_MODERNIZATION_GUIDE.md)
- [CORTX Designer Reference](/cortx-designer/frontend) (fully branded example)
- [Tailwind CSS Docs](https://tailwindcss.com)
- [Radix UI Docs](https://www.radix-ui.com)
- [Recharts Docs](https://recharts.org)
- [Next.js Docs](https://nextjs.org)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

**Last Updated:** 2025-10-06
