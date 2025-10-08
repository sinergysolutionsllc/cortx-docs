# CORTX Navigation System - Quick Start Guide

## Installation

The navigation system is built into the `@sinergysolutions/cortx-ui` package.

```bash
npm install @sinergysolutions/cortx-ui
```

## Quick Start

### 1. Basic Page with Navigation

```tsx
'use client';

import {
  GlobalNavigation,
  DomainNavigation,
  useNavigationContext,
} from '@sinergysolutions/cortx-ui';

export default function MyPage() {
  const { currentDomain } = useNavigationContext();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Global nav bar at the top */}
      <GlobalNavigation
        user={{
          name: "John Doe",
          email: "john@example.com",
        }}
      />

      <div className="flex flex-1">
        {/* Sidebar navigation */}
        <DomainNavigation domain={currentDomain} />

        {/* Your page content */}
        <main className="flex-1 p-8">
          <h1>My Page</h1>
        </main>
      </div>
    </div>
  );
}
```

### 2. Using CortexLink for Navigation

```tsx
import { CortexLink } from '@sinergysolutions/cortx-ui';

function MyComponent() {
  return (
    <div>
      {/* Link using route ID (recommended) */}
      <CortexLink to="platform-designer">
        Open BPM Designer
      </CortexLink>

      {/* Link to another suite */}
      <CortexLink to="fedsuite-fedreconcile">
        Go to FedReconcile
      </CortexLink>

      {/* External link */}
      <CortexLink to="https://example.com" external>
        External Site
      </CortexLink>
    </div>
  );
}
```

### 3. Custom Navigation with Hooks

```tsx
import { useRouteBuilder, useActiveRoute } from '@sinergysolutions/cortx-ui';

function CustomNav() {
  const { buildRouteUrl } = useRouteBuilder();
  const activeRoute = useActiveRoute();

  const handleNavigate = () => {
    const url = buildRouteUrl('platform-marketplace');
    window.location.href = url;
  };

  return (
    <div>
      <p>Current page: {activeRoute?.label}</p>
      <button onClick={handleNavigate}>Go to Marketplace</button>
    </div>
  );
}
```

## Available Route IDs

### Platform (sinergysolutions.ai)

- `platform-dashboard` - Platform Dashboard
- `platform-designer` - BPM Designer
- `platform-marketplace` - Marketplace
- `platform-thinktank` - ThinkTank
- `platform-settings` - Platform Settings
- `platform-settings-identity` - Identity & Access
- `platform-settings-api` - API Keys
- `platform-settings-status` - System Status

### FedSuite (fedsuite.ai)

- `fedsuite-dashboard` - FedSuite Dashboard
- `fedsuite-fedreconcile` - FedReconcile Module
- `fedsuite-feddataflow` - FedDataFlow Module
- `fedsuite-gtas-dashboard` - GTAS Reconciliation Dashboard

### CorpSuite (corpsuite.ai)

- `corpsuite-dashboard` - CorpSuite Dashboard
- `corpsuite-propverify` - PropVerify Module
- `corpsuite-greenlight` - Greenlight Module
- `corpsuite-investmait` - InvestMait Module
- `corpsuite-realestate-dashboard` - Real Estate Portfolio Dashboard

## Development Mode

When running locally, use these ports:

- **Port 3000**: Platform (sinergysolutions.ai)
- **Port 3001**: FedSuite (fedsuite.ai)
- **Port 3002**: CorpSuite (corpsuite.ai)
- **Port 3003**: MedSuite (medsuite.ai)

The navigation system automatically detects the port and builds correct URLs.

## Adding New Routes

1. Open `/packages/cortx-ui/src/config/routes.ts`
2. Add your route to the appropriate array:

```typescript
export const fedSuiteRoutes: Route[] = [
  // ... existing routes
  {
    id: 'fedsuite-new-module',
    path: '/modules/new-module',
    domain: 'fedsuite.ai',
    label: 'New Module',
    icon: 'star',
    suiteModule: 'NewModule',
    description: 'My new module',
    requiresAuth: true,
  },
];
```

3. Rebuild the package: `npm run build`
4. Use the new route: `<CortexLink to="fedsuite-new-module">New Module</CortexLink>`

## Common Patterns

### Full-Page Layout

```tsx
import {
  GlobalNavigation,
  DomainNavigation,
  useNavigationContext,
} from '@sinergysolutions/cortx-ui';

export default function Layout({ children }) {
  const { currentDomain } = useNavigationContext();

  return (
    <div className="min-h-screen flex flex-col">
      <GlobalNavigation
        user={user}
        onSearch={handleSearch}
        onSignOut={handleSignOut}
      />
      <div className="flex flex-1">
        <DomainNavigation domain={currentDomain} />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
```

### Conditional Navigation

```tsx
import { useNavigationContext, CortexLink } from '@sinergysolutions/cortx-ui';

function ConditionalNav() {
  const { currentDomain } = useNavigationContext();

  return (
    <div>
      {currentDomain === 'fedsuite.ai' && (
        <CortexLink to="fedsuite-gtas-dashboard">
          GTAS Dashboard
        </CortexLink>
      )}

      {currentDomain === 'corpsuite.ai' && (
        <CortexLink to="corpsuite-realestate-dashboard">
          Real Estate Dashboard
        </CortexLink>
      )}
    </div>
  );
}
```

### Custom Active Styling

```tsx
import { CortexLink, useIsActiveRoute } from '@sinergysolutions/cortx-ui';
import { cn } from '@sinergysolutions/cortx-ui';

function NavItem({ routeId, label }) {
  const isActive = useIsActiveRoute(routeId);

  return (
    <CortexLink
      to={routeId}
      className={cn(
        'px-4 py-2 rounded',
        isActive
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      )}
    >
      {label}
    </CortexLink>
  );
}
```

## TypeScript Support

All components and hooks are fully typed. Your IDE will provide autocomplete for:

- Route IDs
- Domain names
- Component props
- Hook return values

```typescript
import type {
  Domain,
  Route,
  NavigationContext,
  UserProfile,
  CortexLinkProps,
} from '@sinergysolutions/cortx-ui';
```

## Troubleshooting

### Links not working in development

- Ensure you're running apps on correct ports (3000, 3001, 3002, 3003)
- Check that the target app is actually running

### Active state not highlighting

- Verify the route ID matches exactly
- Check that you're using the correct domain

### TypeScript errors

- Make sure you're importing from `@sinergysolutions/cortx-ui`
- Run `npm run build` in the cortx-ui package after changes

### Cross-domain navigation not working

- Check the route configuration in `/config/routes.ts`
- Verify the domain is correct for the route

## More Information

For detailed documentation, see:

- [Navigation Components README](/packages/cortx-ui/src/components/navigation/README.md)
- [Navigation Strategy Document](/docs/architecture/PROPOSED_NAVIGATION_STRATEGY.md)
