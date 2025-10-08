'use client';

import * as React from 'react';
import { cn } from '../../utils/cn';
import { CortexLink } from './CortexLink';
import { DomainNavigationProps, NavigationItem } from '../../types/navigation';
import { useDomainRoutes, useActiveRoute } from '../../hooks/useNavigation';
import { Route } from '../../config/routes';
import { Button } from '../button';

/**
 * DomainNavigation - Suite-specific sidebar navigation
 *
 * Features:
 * - Renders navigation specific to current domain
 * - Hierarchical menu structure
 * - Active route highlighting
 * - Collapsible sections
 *
 * Layout for FedSuite:
 * +-------------------------+
 * | - Dashboard             |
 * | - Modules               |
 * |   - FedReconcile        |
 * |   - FedDataFlow         |
 * | - Dashboards            |
 * |   - GTAS Reconciliation |
 * +-------------------------+
 *
 * Usage:
 * ```tsx
 * <DomainNavigation domain="fedsuite.ai" />
 * ```
 */

interface NavSection {
  label: string;
  items: NavigationItem[];
  collapsible?: boolean;
}

function groupRoutesBySection(routes: Route[]): NavSection[] {
  const sections: NavSection[] = [];

  // Dashboard section (routes with path '/')
  const dashboardRoutes = routes.filter(r => r.path === '/');
  if (dashboardRoutes.length > 0) {
    sections.push({
      label: 'Dashboard',
      items: dashboardRoutes.map(r => ({
        id: r.id,
        label: r.label,
        href: r.id,
        icon: r.icon,
      })),
      collapsible: false,
    });
  }

  // Modules section (routes with suiteModule)
  const moduleRoutes = routes.filter(r => r.suiteModule);
  if (moduleRoutes.length > 0) {
    sections.push({
      label: 'Modules',
      items: moduleRoutes.map(r => ({
        id: r.id,
        label: r.label,
        href: r.id,
        icon: r.icon,
      })),
      collapsible: true,
    });
  }

  // Dashboards section (routes with path starting with '/dashboards')
  const dashboardsRoutes = routes.filter(r => r.path.startsWith('/dashboards'));
  if (dashboardsRoutes.length > 0) {
    sections.push({
      label: 'Dashboards',
      items: dashboardsRoutes.map(r => ({
        id: r.id,
        label: r.label,
        href: r.id,
        icon: r.icon,
      })),
      collapsible: true,
    });
  }

  // Settings section (routes with path starting with '/settings')
  const settingsRoutes = routes.filter(
    r => r.path.startsWith('/settings') && r.path !== '/settings'
  );
  if (settingsRoutes.length > 0) {
    sections.push({
      label: 'Settings',
      items: settingsRoutes.map(r => ({
        id: r.id,
        label: r.label,
        href: r.id,
        icon: r.icon,
      })),
      collapsible: true,
    });
  }

  return sections;
}

export function DomainNavigation({
  domain,
  activeRoute,
  className,
  showMobile = false,
}: DomainNavigationProps) {
  const routes = useDomainRoutes(domain);
  const currentActiveRoute = useActiveRoute();
  const active = activeRoute || currentActiveRoute;

  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(
    new Set(['Modules', 'Dashboards', 'Settings'])
  );

  const sections = React.useMemo(() => groupRoutesBySection(routes), [routes]);

  const toggleSection = (label: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  if (routes.length === 0) {
    return null;
  }

  return (
    <aside
      className={cn(
        'w-64 border-r border-border bg-background/50',
        'flex flex-col',
        showMobile ? 'block' : 'hidden md:block',
        className
      )}
    >
      <nav className="flex-1 overflow-y-auto p-4 space-y-6">
        {sections.map((section) => {
          const isExpanded = expandedSections.has(section.label);

          return (
            <div key={section.label}>
              {/* Section Header */}
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {section.label}
                </h3>
                {section.collapsible && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0"
                    onClick={() => toggleSection(section.label)}
                  >
                    <svg
                      className={cn(
                        'h-3 w-3 transition-transform',
                        isExpanded ? 'rotate-90' : ''
                      )}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </Button>
                )}
              </div>

              {/* Section Items */}
              {(!section.collapsible || isExpanded) && (
                <div className="space-y-1">
                  {section.items.map((item) => {
                    const isActive = active?.id === item.id;

                    return (
                      <CortexLink
                        key={item.id}
                        to={item.href}
                        active={isActive}
                      >
                        <div
                          className={cn(
                            'flex items-center gap-3 px-3 py-2 rounded-md text-sm',
                            'transition-colors duration-150',
                            isActive
                              ? 'bg-primary text-primary-foreground font-medium'
                              : 'text-foreground hover:bg-accent hover:text-accent-foreground',
                            item.disabled && 'opacity-50 cursor-not-allowed'
                          )}
                        >
                          {item.icon && (
                            <span className="text-current opacity-70">
                              {/* Icon placeholder - would use actual icon library */}
                              <svg
                                className="h-4 w-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <circle cx="12" cy="12" r="3" />
                              </svg>
                            </span>
                          )}
                          <span className="flex-1">{item.label}</span>
                          {item.badge && (
                            <span className="text-xs px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                              {item.badge}
                            </span>
                          )}
                        </div>
                      </CortexLink>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Platform Tools Quick Access */}
      <div className="border-t border-border p-4 space-y-1">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Platform Tools
        </div>
        <CortexLink to="platform-designer">
          <div className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
            <span className="text-current opacity-70">
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
              </svg>
            </span>
            Designer
          </div>
        </CortexLink>
        <CortexLink to="platform-marketplace">
          <div className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
            <span className="text-current opacity-70">
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
                />
              </svg>
            </span>
            Marketplace
          </div>
        </CortexLink>
      </div>
    </aside>
  );
}

DomainNavigation.displayName = 'DomainNavigation';
