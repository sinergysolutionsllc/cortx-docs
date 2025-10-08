# CORTX Navigation System

A comprehensive, domain-driven navigation system for the CORTX platform, supporting seamless navigation across multiple suite domains.

## Overview

The CORTX navigation system provides:

- **Cross-domain navigation** between sinergysolutions.ai, fedsuite.ai, and corpsuite.ai
- **Centralized route configuration** as single source of truth
- **Type-safe navigation** with TypeScript autocomplete
- **Active route detection** for highlighting current page
- **Development mode support** with localhost port-based routing
- **Responsive design** with mobile-friendly navigation

## Domain Structure

```
sinergysolutions.ai (Core Platform)
├── Platform Dashboard
├── BPM Designer
├── Marketplace
├── ThinkTank
└── Settings

fedsuite.ai (Federal Suite)
├── FedSuite Dashboard
├── Modules
│   ├── FedReconcile
│   └── FedDataFlow
└── Dashboards
    └── GTAS Reconciliation

corpsuite.ai (Corporate Suite)
├── CorpSuite Dashboard
├── Modules
│   ├── PropVerify
│   ├── Greenlight
│   └── InvestMait
└── Dashboards
    └── Real Estate Portfolio
```

## Components

### CortexLink

Smart link component that handles cross-domain navigation automatically.

```tsx
import { CortexLink } from '@sinergysolutions/cortx-ui';

// Using route ID (recommended)
<CortexLink to="platform-designer">
  BPM Designer
</CortexLink>

// Using full path
<CortexLink to="/modules/fedreconcile">
  FedReconcile
</CortexLink>

// External link
<CortexLink to="https://example.com" external>
  External Site
</CortexLink>

// Active state styling
<CortexLink to="platform-marketplace" className="nav-link">
  Marketplace
</CortexLink>
```

**Props:**

- `to` (string, required): Route ID or URL
- `children` (ReactNode, required): Link content
- `className` (string): Additional CSS classes
- `target` (LinkTarget): Link target (_self,_blank, etc.)
- `external` (boolean): Whether this is an external link
- `prefetch` (boolean): Whether to prefetch the route (Next.js)
- `active` (boolean): Override active state
- `onClick` (function): Click handler

### GlobalNavigation

Persistent navigation bar across all domains.

```tsx
import { GlobalNavigation } from '@sinergysolutions/cortx-ui';

<GlobalNavigation
  user={{
    name: "John Doe",
    email: "john@example.com",
    avatarUrl: "/avatar.jpg",
    role: "Administrator"
  }}
  onSearch={(query) => handleSearch(query)}
  onSignOut={() => handleSignOut()}
  showSearch={true}
/>
```

**Features:**

- Sinergy logo linking to platform
- Suite switcher dropdown
- Quick access to Designer, Marketplace, ThinkTank
- Global search bar (with ⌘K shortcut placeholder)
- User profile display
- Mobile-responsive with hamburger menu

**Props:**

- `user` (UserProfile): User information
- `onSearch` (function): Search handler
- `onSignOut` (function): Sign out handler
- `showSearch` (boolean): Show/hide search bar
- `showMobile` (boolean): Enable mobile menu
- `className` (string): Additional CSS classes

### SuiteSwitcher

Dropdown for switching between suite domains.

```tsx
import { SuiteSwitcher } from '@sinergysolutions/cortx-ui';

<SuiteSwitcher
  currentDomain="fedsuite.ai"
  onSuiteChange={(domain) => console.log('Switched to:', domain)}
/>
```

**Features:**

- Shows all available suites
- Indicates coming soon suites (MedSuite)
- Handles cross-domain navigation
- Displays suite descriptions

**Props:**

- `currentDomain` (Domain, required): Current active domain
- `onSuiteChange` (function): Callback when suite changes
- `className` (string): Additional CSS classes

### DomainNavigation

Suite-specific sidebar navigation.

```tsx
import { DomainNavigation } from '@sinergysolutions/cortx-ui';

<DomainNavigation
  domain="fedsuite.ai"
  className="sidebar"
/>
```

**Features:**

- Context-aware navigation based on domain
- Hierarchical menu structure (Dashboard, Modules, Dashboards)
- Collapsible sections
- Active route highlighting
- Quick access to platform tools
- Mobile-responsive

**Props:**

- `domain` (Domain, required): Domain to render navigation for
- `activeRoute` (Route): Current active route
- `className` (string): Additional CSS classes
- `showMobile` (boolean): Show mobile navigation

## Hooks

### useNavigationContext

Get current navigation context.

```tsx
import { useNavigationContext } from '@sinergysolutions/cortx-ui';

function MyComponent() {
  const { currentDomain, currentPath, isDevelopment } = useNavigationContext();

  return <div>Current domain: {currentDomain}</div>;
}
```

**Returns:**

- `currentDomain` (Domain): Current domain
- `currentPath` (string): Current path
- `isDevelopment` (boolean): Whether in development mode
- `activeModule` (string): Active module if applicable

### useRouteBuilder

Build URLs for routes.

```tsx
import { useRouteBuilder } from '@sinergysolutions/cortx-ui';

function MyComponent() {
  const { buildRouteUrl, buildUrl, isSameDomain } = useRouteBuilder();

  const designerUrl = buildRouteUrl('platform-designer');
  const customUrl = buildUrl('fedsuite.ai', '/custom-path');
  const sameD = isSameDomain('platform-marketplace');

  return <a href={designerUrl}>Designer</a>;
}
```

**Returns:**

- `buildRouteUrl(routeId)`: Build URL from route ID
- `buildUrl(domain, path)`: Build URL from domain and path
- `isSameDomain(routeId)`: Check if route is on current domain
- `currentDomain`: Current domain
- `isDevelopment`: Development mode flag

### useActiveRoute

Get the current active route.

```tsx
import { useActiveRoute } from '@sinergysolutions/cortx-ui';

function MyComponent() {
  const activeRoute = useActiveRoute();

  return <h1>{activeRoute?.label || 'Not Found'}</h1>;
}
```

### useIsActiveRoute

Check if a specific route is active.

```tsx
import { useIsActiveRoute } from '@sinergysolutions/cortx-ui';

function NavItem({ routeId }) {
  const isActive = useIsActiveRoute(routeId);

  return (
    <div className={isActive ? 'active' : ''}>
      {/* Nav item content */}
    </div>
  );
}
```

### useDomainRoutes

Get routes for a specific domain.

```tsx
import { useDomainRoutes } from '@sinergysolutions/cortx-ui';

function SidebarNav() {
  const routes = useDomainRoutes('fedsuite.ai');

  return (
    <ul>
      {routes.map(route => (
        <li key={route.id}>{route.label}</li>
      ))}
    </ul>
  );
}
```

## Route Configuration

All routes are defined in `config/routes.ts` as a single source of truth.

### Adding a New Route

```typescript
// In config/routes.ts
export const fedSuiteRoutes: Route[] = [
  // ... existing routes
  {
    id: 'fedsuite-new-module',
    path: '/modules/new-module',
    domain: 'fedsuite.ai',
    label: 'New Module',
    icon: 'star',
    suiteModule: 'NewModule',
    description: 'Description of new module',
    requiresAuth: true,
  },
];
```

### Route Interface

```typescript
interface Route {
  id: string;                    // Unique identifier
  path: string;                  // Path within domain
  domain: Domain;                // Domain this route belongs to
  label: string;                 // Human-readable label
  icon?: string;                 // Icon identifier
  suiteModule?: SuiteModule;     // Suite module if applicable
  description?: string;          // Description for tooltips
  requiresAuth?: boolean;        // Authentication requirement
}
```

## Development Mode

The navigation system supports localhost development with port-based routing:

- **Port 3000**: sinergysolutions.ai (Platform)
- **Port 3001**: fedsuite.ai (Federal Suite)
- **Port 3002**: corpsuite.ai (Corporate Suite)
- **Port 3003**: medsuite.ai (Medical Suite)

The system automatically detects development mode and generates appropriate localhost URLs.

## Production Deployment

In production, the navigation system generates full domain URLs:

- `https://sinergysolutions.ai/designer`
- `https://fedsuite.ai/modules/fedreconcile`
- `https://corpsuite.ai/modules/propverify`

## Complete Example

Here's a complete example of a page with full navigation:

```tsx
'use client';

import {
  GlobalNavigation,
  DomainNavigation,
  CortexLink,
  useNavigationContext,
} from '@sinergysolutions/cortx-ui';

export default function MyPage() {
  const { currentDomain } = useNavigationContext();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Global navigation bar */}
      <GlobalNavigation
        user={{
          name: "John Doe",
          email: "john@example.com",
        }}
        onSearch={(q) => console.log('Search:', q)}
        onSignOut={() => console.log('Sign out')}
      />

      <div className="flex flex-1">
        {/* Sidebar navigation */}
        <DomainNavigation domain={currentDomain} />

        {/* Main content */}
        <main className="flex-1 p-8">
          <h1>Welcome to FedSuite</h1>

          <div className="space-x-4">
            <CortexLink to="fedsuite-fedreconcile">
              Go to FedReconcile
            </CortexLink>

            <CortexLink to="platform-designer">
              Open BPM Designer
            </CortexLink>
          </div>
        </main>
      </div>
    </div>
  );
}
```

## TypeScript Support

All components and hooks are fully typed with TypeScript. Route IDs will be autocompleted in your IDE when using `CortexLink` with route IDs.

```typescript
import type {
  Domain,
  Route,
  NavigationContext,
  UserProfile,
} from '@sinergysolutions/cortx-ui';
```

## Styling

All components use Tailwind CSS with the CORTX design system. They support custom className props for additional styling.

## Accessibility

The navigation system includes:

- ARIA labels for screen readers
- Keyboard navigation support
- Focus indicators
- Semantic HTML structure
- Responsive design for all screen sizes

## Best Practices

1. **Always use CortexLink** instead of regular `<a>` or Next.js `<Link>` for internal navigation
2. **Use route IDs** instead of hardcoded paths when possible
3. **Add new routes to config/routes.ts** to maintain the single source of truth
4. **Test cross-domain navigation** in both development and production environments
5. **Use the navigation hooks** to get current context instead of manual window.location checks

## Troubleshooting

### Links not working in development

Make sure you're running the apps on the correct ports:

- Platform: `npm run dev` on port 3000
- FedSuite: `npm run dev` on port 3001
- CorpSuite: `npm run dev` on port 3002

### Active state not highlighting

Ensure the route ID matches exactly in both the route configuration and the CortexLink component.

### Cross-domain navigation not working

Check that the domain is correctly configured in the route definition and that the target application is running (in development) or deployed (in production).
