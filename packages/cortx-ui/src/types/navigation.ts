/**
 * Navigation Type Definitions
 *
 * Shared types for the CORTX navigation system
 */

import { Domain, Route } from '../config/routes';

/**
 * Navigation context providing current domain and route information
 */
export interface NavigationContext {
  /** Current domain the user is on */
  currentDomain: Domain;
  /** Current route path */
  currentPath: string;
  /** Whether we're in development mode (localhost) */
  isDevelopment: boolean;
  /** Active suite module, if applicable */
  activeModule?: string;
}

/**
 * Props for navigation components
 */
export interface NavigationProps {
  /** Additional CSS classes */
  className?: string;
  /** Whether to show mobile navigation */
  showMobile?: boolean;
}

/**
 * User profile information for the navigation
 */
export interface UserProfile {
  /** User's full name */
  name: string;
  /** User's email address */
  email: string;
  /** URL to user's avatar image */
  avatarUrl?: string;
  /** User's role or title */
  role?: string;
}

/**
 * Props for user menu component
 */
export interface UserMenuProps {
  user: UserProfile;
  onSignOut?: () => void;
  className?: string;
}

/**
 * Navigation item for rendering in menus
 */
export interface NavigationItem {
  /** Unique identifier */
  id: string;
  /** Display label */
  label: string;
  /** URL or route ID */
  href: string;
  /** Icon identifier */
  icon?: string;
  /** Whether this item is currently active */
  active?: boolean;
  /** Child navigation items */
  children?: NavigationItem[];
  /** Whether this item is disabled */
  disabled?: boolean;
  /** Badge text (e.g., "New", "Beta") */
  badge?: string;
}

/**
 * Props for suite switcher component
 */
export interface SuiteSwitcherProps {
  /** Current active domain */
  currentDomain: Domain;
  /** Callback when suite is changed */
  onSuiteChange?: (domain: Domain) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Props for domain navigation component
 */
export interface DomainNavigationProps extends NavigationProps {
  /** Current domain to render navigation for */
  domain: Domain;
  /** Current active route */
  activeRoute?: Route;
}

/**
 * Link target for navigation
 */
export type LinkTarget = '_self' | '_blank' | '_parent' | '_top';

/**
 * Props for CortexLink component
 */
export interface CortexLinkProps {
  /** Route ID or full URL */
  to: string;
  /** Link content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Link target */
  target?: LinkTarget;
  /** Whether to open in new tab */
  external?: boolean;
  /** Whether to prefetch the route (Next.js specific) */
  prefetch?: boolean;
  /** Whether this link is currently active */
  active?: boolean;
  /** Callback when link is clicked */
  onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
}

/**
 * Search result for global search
 */
export interface SearchResult {
  /** Unique identifier */
  id: string;
  /** Result title */
  title: string;
  /** Result description */
  description?: string;
  /** Route or URL to navigate to */
  href: string;
  /** Type of result (page, module, action, etc.) */
  type: 'page' | 'module' | 'action' | 'document' | 'user';
  /** Icon identifier */
  icon?: string;
}

/**
 * Props for global search component
 */
export interface GlobalSearchProps {
  /** Placeholder text */
  placeholder?: string;
  /** Callback when search is performed */
  onSearch?: (query: string) => void;
  /** Search results */
  results?: SearchResult[];
  /** Whether search is loading */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
}
