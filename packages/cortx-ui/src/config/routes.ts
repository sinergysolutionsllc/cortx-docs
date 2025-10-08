/**
 * Centralized Route Configuration for CORTX Platform
 *
 * This file serves as the single source of truth for all routes across
 * the CORTX platform and its domain-specific suites.
 *
 * Domain Structure:
 * - sinergysolutions.ai: Core platform hub
 * - fedsuite.ai: Federal suite domain
 * - corpsuite.ai: Corporate suite domain
 * - medsuite.ai: Medical suite domain (future)
 */

export type Domain = 'sinergysolutions.ai' | 'fedsuite.ai' | 'corpsuite.ai' | 'medsuite.ai';

export type SuiteModule =
  // Federal Suite Modules
  | 'FedReconcile'
  | 'FedDataFlow'
  // Corporate Suite Modules
  | 'PropVerify'
  | 'Greenlight'
  | 'InvestMait'
  // Medical Suite Modules (future)
  | 'MedVerify'
  | 'MedDataFlow';

export interface Route {
  /** Unique identifier for the route */
  id: string;
  /** The path within the domain (e.g., '/designer', '/modules/fedreconcile') */
  path: string;
  /** The domain this route belongs to */
  domain: Domain;
  /** Human-readable label for navigation */
  label: string;
  /** Optional icon identifier (for use with icon libraries) */
  icon?: string;
  /** Optional suite module this route belongs to */
  suiteModule?: SuiteModule;
  /** Optional description for tooltips/documentation */
  description?: string;
  /** Whether this route requires authentication */
  requiresAuth?: boolean;
}

/**
 * Core Platform Routes (sinergysolutions.ai)
 */
export const platformRoutes: Route[] = [
  {
    id: 'platform-dashboard',
    path: '/',
    domain: 'sinergysolutions.ai',
    label: 'Platform Dashboard',
    icon: 'home',
    description: 'CORTX Platform central hub',
    requiresAuth: true,
  },
  {
    id: 'platform-designer',
    path: '/designer',
    domain: 'sinergysolutions.ai',
    label: 'BPM Designer',
    icon: 'cube',
    description: 'Business Process Management Designer',
    requiresAuth: true,
  },
  {
    id: 'platform-marketplace',
    path: '/marketplace',
    domain: 'sinergysolutions.ai',
    label: 'Marketplace',
    icon: 'shopping-bag',
    description: 'RulePacks and WorkflowPacks marketplace',
    requiresAuth: true,
  },
  {
    id: 'platform-thinktank',
    path: '/thinktank',
    domain: 'sinergysolutions.ai',
    label: 'ThinkTank',
    icon: 'sparkles',
    description: 'Platform-level AI assistant',
    requiresAuth: true,
  },
  {
    id: 'platform-settings',
    path: '/settings',
    domain: 'sinergysolutions.ai',
    label: 'Platform Settings',
    icon: 'cog',
    requiresAuth: true,
  },
  {
    id: 'platform-settings-identity',
    path: '/settings/identity',
    domain: 'sinergysolutions.ai',
    label: 'Identity & Access',
    description: 'Manage users and permissions',
    requiresAuth: true,
  },
  {
    id: 'platform-settings-api',
    path: '/settings/api-keys',
    domain: 'sinergysolutions.ai',
    label: 'API Keys',
    description: 'Manage API keys and integrations',
    requiresAuth: true,
  },
  {
    id: 'platform-settings-status',
    path: '/settings/status',
    domain: 'sinergysolutions.ai',
    label: 'System Status',
    description: 'View system health and status',
    requiresAuth: true,
  },
];

/**
 * Federal Suite Routes (fedsuite.ai)
 */
export const fedSuiteRoutes: Route[] = [
  {
    id: 'fedsuite-dashboard',
    path: '/',
    domain: 'fedsuite.ai',
    label: 'FedSuite Dashboard',
    icon: 'home',
    description: 'Federal suite dashboard',
    requiresAuth: true,
  },
  {
    id: 'fedsuite-fedreconcile',
    path: '/modules/fedreconcile',
    domain: 'fedsuite.ai',
    label: 'FedReconcile',
    icon: 'check-circle',
    suiteModule: 'FedReconcile',
    description: 'Federal reconciliation module',
    requiresAuth: true,
  },
  {
    id: 'fedsuite-feddataflow',
    path: '/modules/feddataflow',
    domain: 'fedsuite.ai',
    label: 'FedDataFlow',
    icon: 'arrows-right-left',
    suiteModule: 'FedDataFlow',
    description: 'Federal data transformation and flow',
    requiresAuth: true,
  },
  {
    id: 'fedsuite-gtas-dashboard',
    path: '/dashboards/gtas-reconciliation',
    domain: 'fedsuite.ai',
    label: 'GTAS Reconciliation Dashboard',
    icon: 'chart-bar',
    description: 'GTAS reconciliation analytics',
    requiresAuth: true,
  },
];

/**
 * Corporate Suite Routes (corpsuite.ai)
 */
export const corpSuiteRoutes: Route[] = [
  {
    id: 'corpsuite-dashboard',
    path: '/',
    domain: 'corpsuite.ai',
    label: 'CorpSuite Dashboard',
    icon: 'home',
    description: 'Corporate suite dashboard',
    requiresAuth: true,
  },
  {
    id: 'corpsuite-propverify',
    path: '/modules/propverify',
    domain: 'corpsuite.ai',
    label: 'PropVerify',
    icon: 'building-office',
    suiteModule: 'PropVerify',
    description: 'Property verification module',
    requiresAuth: true,
  },
  {
    id: 'corpsuite-greenlight',
    path: '/modules/greenlight',
    domain: 'corpsuite.ai',
    label: 'Greenlight',
    icon: 'check-badge',
    suiteModule: 'Greenlight',
    description: 'Project approval and tracking',
    requiresAuth: true,
  },
  {
    id: 'corpsuite-investmait',
    path: '/modules/investmait',
    domain: 'corpsuite.ai',
    label: 'InvestMait',
    icon: 'chart-pie',
    suiteModule: 'InvestMait',
    description: 'Investment maintenance tracking',
    requiresAuth: true,
  },
  {
    id: 'corpsuite-realestate-dashboard',
    path: '/dashboards/real-estate-portfolio',
    domain: 'corpsuite.ai',
    label: 'Real Estate Portfolio Dashboard',
    icon: 'chart-bar',
    description: 'Real estate portfolio analytics',
    requiresAuth: true,
  },
];

/**
 * Medical Suite Routes (medsuite.ai) - Future
 */
export const medSuiteRoutes: Route[] = [
  {
    id: 'medsuite-dashboard',
    path: '/',
    domain: 'medsuite.ai',
    label: 'MedSuite Dashboard',
    icon: 'home',
    description: 'Medical suite dashboard',
    requiresAuth: true,
  },
  // Additional medical suite routes will be added as needed
];

/**
 * Combined routes from all domains
 */
export const allRoutes: Route[] = [
  ...platformRoutes,
  ...fedSuiteRoutes,
  ...corpSuiteRoutes,
  ...medSuiteRoutes,
];

/**
 * Suite information for the suite switcher
 */
export interface SuiteInfo {
  domain: Domain;
  name: string;
  label: string;
  description: string;
  icon?: string;
  available: boolean;
}

export const suites: SuiteInfo[] = [
  {
    domain: 'fedsuite.ai',
    name: 'FedSuite',
    label: 'Federal Suite',
    description: 'Federal government solutions',
    icon: 'shield-check',
    available: true,
  },
  {
    domain: 'corpsuite.ai',
    name: 'CorpSuite',
    label: 'Corporate Suite',
    description: 'Corporate and enterprise solutions',
    icon: 'building-office-2',
    available: true,
  },
  {
    domain: 'medsuite.ai',
    name: 'MedSuite',
    label: 'Medical Suite',
    description: 'Healthcare and medical solutions',
    icon: 'heart',
    available: false, // Coming soon
  },
];

/**
 * Helper function to get routes by domain
 */
export function getRoutesByDomain(domain: Domain): Route[] {
  return allRoutes.filter(route => route.domain === domain);
}

/**
 * Helper function to get a route by ID
 */
export function getRouteById(id: string): Route | undefined {
  return allRoutes.find(route => route.id === id);
}

/**
 * Helper function to get routes by suite module
 */
export function getRoutesByModule(suiteModule: SuiteModule): Route[] {
  return allRoutes.filter(route => route.suiteModule === suiteModule);
}

/**
 * Helper function to validate if a path exists for a given domain
 */
export function isValidRoute(domain: Domain, path: string): boolean {
  return allRoutes.some(route => route.domain === domain && route.path === path);
}
