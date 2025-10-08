/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Official Sinergy Brand Palette
        'sinergy-teal': '#00C2CB',
        'federal-navy': '#2D5972',
        'clarity-blue': '#E5FCFF',
        'slate-gray': '#8CAABF',

        // Expanded shades for UI design
        'navy': {
          '50': '#f0f5f9',
          '100': '#e0eaf2',
          '200': '#c8dae6',
          '300': '#a7c3d7',
          '400': '#83a8c3',
          '500': '#698eab',
          '600': '#557490',
          '700': '#455e76',
          '800': '#394d60',
          '900': '#2d5972',
          '950': '#1f3443',
        },
        'teal': {
          '50': '#f0fcfc',
          '100': '#cffafa',
          '200': '#a9f5f6',
          '300': '#72edef',
          '400': '#34e1e6',
          '500': '#00c2cb',
          '600': '#00a0a8',
          '700': '#008187',
          '800': '#00666b',
          '900': '#005459',
          '950': '#003538',
        }
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        heading: ['"Space Grotesk"', 'sans-serif'],
        subtitle: ['"DM Sans"', 'sans-serif'],
        subheading: ['Manrope', 'sans-serif'],
        'section-header': ['Sora', 'sans-serif'],
        quote: ['Lora', 'serif'],
        caption: ['Roboto', 'sans-serif'],
      },
      boxShadow: {
        'apple': '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',
        'apple-md': '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
        'apple-lg': '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
        'apple-xl': '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
}
