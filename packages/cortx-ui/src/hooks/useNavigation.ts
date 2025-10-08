'use client';

import { useEffect, useState, useMemo } from 'react';
import { Domain, Route, getRouteById, getRoutesByDomain } from '../config/routes';
import { NavigationContext } from '../types/navigation';

/**
 * Detect the current domain from hostname
 */
export function detectDomain(hostname: string): Domain {
  // Handle localhost development
  if (hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
    // Check for port-based routing in development
    // Port 3000 = platform, 3001 = fedsuite, 3002 = corpsuite, etc.
    const port = window.location.port;
    switch (port) {
      case '3001':
        return 'fedsuite.ai';
      case '3002':
        return 'corpsuite.ai';
      case '3003':
        return 'medsuite.ai';
      default:
        return 'sinergysolutions.ai';
    }
  }

  // Production domain detection
  if (hostname.includes('fedsuite.ai')) return 'fedsuite.ai';
  if (hostname.includes('corpsuite.ai')) return 'corpsuite.ai';
  if (hostname.includes('medsuite.ai')) return 'medsuite.ai';

  // Default to platform
  return 'sinergysolutions.ai';
}

/**
 * Build a full URL for a given domain and path
 */
export function buildUrl(domain: Domain, path: string, isDevelopment: boolean = false): string {
  if (isDevelopment) {
    // Map domains to development ports
    const portMap: Record<Domain, string> = {
      'sinergysolutions.ai': '3000',
      'fedsuite.ai': '3001',
      'corpsuite.ai': '3002',
      'medsuite.ai': '3003',
    };

    const port = portMap[domain];
    return `http://localhost:${port}${path}`;
  }

  // Production URLs
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'https' : 'https';
  return `${protocol}://${domain}${path}`;
}

/**
 * Hook to get navigation context
 */
export function useNavigationContext(): NavigationContext {
  const [context, setContext] = useState<NavigationContext>(() => {
    if (typeof window === 'undefined') {
      return {
        currentDomain: 'sinergysolutions.ai',
        currentPath: '/',
        isDevelopment: false,
      };
    }

    const hostname = window.location.hostname;
    const currentDomain = detectDomain(hostname);
    const isDevelopment = hostname.includes('localhost') || hostname.includes('127.0.0.1');

    return {
      currentDomain,
      currentPath: window.location.pathname,
      isDevelopment,
    };
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const updateContext = () => {
      const hostname = window.location.hostname;
      const currentDomain = detectDomain(hostname);
      const isDevelopment = hostname.includes('localhost') || hostname.includes('127.0.0.1');

      setContext({
        currentDomain,
        currentPath: window.location.pathname,
        isDevelopment,
      });
    };

    // Update on route changes
    window.addEventListener('popstate', updateContext);

    return () => {
      window.removeEventListener('popstate', updateContext);
    };
  }, []);

  return context;
}

/**
 * Hook to build URLs for routes
 */
export function useRouteBuilder() {
  const { currentDomain, isDevelopment } = useNavigationContext();

  return useMemo(() => ({
    /**
     * Build a URL from a route ID
     */
    buildRouteUrl: (routeId: string): string => {
      const route = getRouteById(routeId);
      if (!route) {
        console.warn(`Route not found: ${routeId}`);
        return '#';
      }

      return buildUrl(route.domain, route.path, isDevelopment);
    },

    /**
     * Build a URL from domain and path
     */
    buildUrl: (domain: Domain, path: string): string => {
      return buildUrl(domain, path, isDevelopment);
    },

    /**
     * Check if a route is on the current domain
     */
    isSameDomain: (routeId: string): boolean => {
      const route = getRouteById(routeId);
      return route?.domain === currentDomain;
    },

    /**
     * Get the current domain
     */
    currentDomain,

    /**
     * Check if in development mode
     */
    isDevelopment,
  }), [currentDomain, isDevelopment]);
}

/**
 * Hook to get current active route
 */
export function useActiveRoute(): Route | undefined {
  const { currentDomain, currentPath } = useNavigationContext();

  return useMemo(() => {
    const domainRoutes = getRoutesByDomain(currentDomain);
    return domainRoutes.find(route => route.path === currentPath);
  }, [currentDomain, currentPath]);
}

/**
 * Hook to check if a route is currently active
 */
export function useIsActiveRoute(routeId: string): boolean {
  const activeRoute = useActiveRoute();
  return activeRoute?.id === routeId;
}

/**
 * Hook to get domain-specific routes for navigation
 */
export function useDomainRoutes(domain?: Domain) {
  const { currentDomain } = useNavigationContext();
  const targetDomain = domain || currentDomain;

  return useMemo(() => {
    return getRoutesByDomain(targetDomain);
  }, [targetDomain]);
}
