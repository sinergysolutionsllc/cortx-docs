Sinergy Solutions – UI Modernization Guide

Overview

The Sinergy Solutions UI Modernization Guide provides a consistent framework for building, styling, and maintaining applications such as Greenlight and the broader Sinergy product suite. It ensures that every application reflects Sinergy’s brand identity, leverages modern UI/UX principles, and aligns with accessibility and compliance standards.

⸻

Core Principles
 • Consistency Across Products
All Sinergy apps (Greenlight, FedSuite, ClaimSuite, MedSuite, etc.) must follow the same branding, typography, and color guidelines.
 • Simplicity & Clarity
Reduce clutter, focus on usability, and present complex workflows with guided, intuitive UI elements.
 • Accessibility First
Ensure WCAG AA+ compliance, strong color contrast, and scalable typography for inclusive design.
 • Future-Proofing
Use responsive layouts, dark mode, and modular components to keep applications adaptive across devices.

⸻

Brand Identity

Logos
 • Primary Logo: SS_Logo_Transparent.png
 • Icon Variant: SS-Icon-Transparent.png

Use the full logo in navigation bars, splash screens, and landing pages. Use the icon for favicons, mobile nav, or tight spaces.

Colors

From [brand color file] :
 • Primary Colors
 • Sinergy Teal: #00C2CB
 • Federal Navy: #2D5972
 • Accent Colors
 • Clarity Blue: #E5FCFF
 • Slate Gray: #8CAABF
 • Shades
Full navy/teal shade spectrum available for hover states, gradients, shadows, and overlays.

Usage Notes:
 • Use Sinergy Teal and Federal Navy for buttons, headers, and CTAs.
 • Use Clarity Blue and Slate Gray for backgrounds, highlights, and charts.
 • Maintain WCAG AA contrast when overlaying text.

Typography

From [brand fonts file] :
 • Headings (H1/H2): Space Grotesk
 • Subtitles & Buttons: DM Sans
 • Sub-Headings: Manrope or Sora
 • Body: IBM Plex Sans
 • Quotes: Lora
 • Captions/Labels: Roboto

Implementation:
@import url('<https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;600&family=Manrope:wght@400;500;600;700&family=Sora:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Lora:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap>');

Modernization Features
 • Component Library
Use React + Tailwind UI with reusable cards, modals, and charts.
Each component must have dark/light mode variants.
 • Workflow Wizards
Guided multi-step flows for complex actions (e.g., RFP Template Generation, Opportunity Ingestion).
 • AI Assistance
Embedded RAG + LLM helper panels with citations and context-based recommendations.
 • Documentation Output
Every process (config, checklist, template) should be exportable to PDF/DOCX with Sinergy branding.
 • Analytics Dashboards
Heatmaps, scorecards, and pricing bands styled with Sinergy’s palette and typography.

⸻

Folder Structure (Recommended)

/ui/
  /components/
  /layouts/
  /styles/
    colors.css
    typography.css
  /assets/
    SS_Logo_Transparent.png
    SS-Icon-Transparent.png
  /docs/
    UI_MODERNIZATION_GUIDE.md

uick Start for Developers
 1. Install Fonts
Use sinergy_brand_fonts.txt for proper import and hierarchy.
 2. Apply Colors
Import palette tokens from sinergy_brand_colors_full.txt.
 3. Set Up Tailwind
Configure brand colors and fonts in tailwind.config.js.
 4. Test Accessibility
Run Lighthouse or axe-core audits for contrast, labels, and ARIA coverage.
 5. Brand Verification
Check pages against Sinergy’s logo, colors, and typography — no off-brand deviations.

⸻

References
 • Sinergy Brand Fonts: [sinergy_brand_fonts.txt]
 • Sinergy Brand Colors: [sinergy_brand_colors_full.txt]
 • WCAG 2.1 Guidelines: W3C Accessibility Standards
 • Tailwind CSS: tailwindcss.com
