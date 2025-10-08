# @sinergysolutions/cortx-ui

Shared UI component library for CORTX applications with Sinergy Solutions branding.

## Features

- ✅ **Sinergy Brand Colors**: Teal (#00C2CB), Federal Navy (#2D5972), Clarity Blue, Slate Gray
- ✅ **Brand Typography**: 7 font families (Space Grotesk, DM Sans, IBM Plex Sans, etc.)
- ✅ **Dark Mode Support**: CSS custom properties with light/dark variants
- ✅ **WCAG AA Accessible**: Screen reader support, keyboard navigation, high contrast
- ✅ **TypeScript**: Full type definitions
- ✅ **Tree-shakeable**: ESM/CJS builds with optimized bundle sizes
- ✅ **Tailwind CSS**: Utility-first styling with brand preset

## Installation

```bash
npm install @sinergysolutions/cortx-ui
# or
yarn add @sinergysolutions/cortx-ui
# or
pnpm add @sinergysolutions/cortx-ui
```

### Peer Dependencies

```bash
npm install @radix-ui/react-slot class-variance-authority clsx tailwind-merge tailwindcss
```

## Usage

### 1. Import Tailwind Preset

In your `tailwind.config.js`:

```javascript
module.exports = {
  presets: [require('@sinergysolutions/cortx-ui/tailwind-preset')],
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@sinergysolutions/cortx-ui/dist/**/*.{js,mjs}',
  ],
  // ... rest of your config
}
```

### 2. Add CSS Variables

In your `globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Sinergy Brand Colors */
    --sinergy-teal: #00C2CB;
    --federal-navy: #2D5972;
    --clarity-blue: #E5FCFF;
    --slate-gray: #8CAABF;

    /* Light mode theme */
    --background: 0 0% 100%;
    --foreground: 207 29% 15%;
    --primary: 183 100% 40%; /* Sinergy Teal */
    --primary-foreground: 0 0% 100%;
    --secondary: 207 29% 35%; /* Federal Navy */
    --secondary-foreground: 0 0% 100%;
    --muted: 207 15% 96%;
    --muted-foreground: 207 15% 45%;
    --accent: 183 100% 95%;
    --accent-foreground: 183 100% 40%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 100%;
    --border: 207 15% 90%;
    --input: 207 15% 90%;
    --ring: 183 100% 40%;
    --radius: 0.75rem;
  }

  .dark {
    --background: 210 45% 8%;
    --foreground: 0 0% 100%;
    --primary: 183 100% 40%;
    --primary-foreground: 0 0% 100%;
    --secondary: 207 29% 35%;
    --secondary-foreground: 0 0% 100%;
    --muted: 207 29% 25%;
    --muted-foreground: 207 15% 65%;
    --accent: 183 100% 40%;
    --accent-foreground: 0 0% 100%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 100%;
    --border: 207 29% 30%;
    --input: 207 29% 25%;
    --ring: 183 100% 40%;
  }
}

@layer base {
  body {
    @apply bg-background text-foreground;
    font-family: 'IBM Plex Sans', sans-serif;
  }
}
```

### 3. Use Components

```tsx
import { Button, Input } from '@sinergysolutions/cortx-ui'

export default function MyPage() {
  return (
    <div>
      <Button variant="default">Primary Button</Button>
      <Button variant="secondary">Secondary Button</Button>
      <Button variant="outline">Outline Button</Button>
      <Button variant="ghost">Ghost Button</Button>

      <Input type="email" placeholder="Enter email..." />
    </div>
  )
}
```

## Components

### Button

```tsx
<Button variant="default" size="default">
  Click me
</Button>
```

**Variants**: `default` | `destructive` | `outline` | `secondary` | `ghost` | `link`

**Sizes**: `default` | `sm` | `lg` | `icon`

### Input

```tsx
<Input type="text" placeholder="Type here..." />
```

## Development

```bash
# Install dependencies
npm install

# Build library
npm run build

# Watch mode for development
npm run dev

# Type checking
npm run type-check
```

## License

MIT © Sinergy Solutions LLC
