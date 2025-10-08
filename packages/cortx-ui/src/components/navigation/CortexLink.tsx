'use client';

import * as React from 'react';
import Link from 'next/link';
import { cn } from '../../utils/cn';
import { useRouteBuilder, useIsActiveRoute } from '../../hooks/useNavigation';
import { CortexLinkProps } from '../../types/navigation';

/**
 * CortexLink - Smart link component for cross-domain navigation
 *
 * Features:
 * - Automatically handles cross-domain navigation
 * - Validates routes at build time
 * - Supports both route IDs and full URLs
 * - Active state detection
 * - TypeScript autocomplete for route IDs
 *
 * Usage:
 * ```tsx
 * // Using route ID (recommended)
 * <CortexLink to="platform-designer">BPM Designer</CortexLink>
 *
 * // Using full URL
 * <CortexLink to="https://fedsuite.ai/modules/fedreconcile">FedReconcile</CortexLink>
 *
 * // External link
 * <CortexLink to="https://example.com" external>External Site</CortexLink>
 * ```
 */
export const CortexLink = React.forwardRef<HTMLAnchorElement, CortexLinkProps>(
  (
    {
      to,
      children,
      className,
      target,
      external = false,
      prefetch = true,
      active,
      onClick,
      ...props
    },
    ref
  ) => {
    const { buildRouteUrl, isSameDomain } = useRouteBuilder();

    // Determine if 'to' is a route ID or a URL
    const isRouteId = !to.startsWith('http') && !to.startsWith('/');
    const isExternalLink = external || to.startsWith('http');

    // Build the href
    const href = React.useMemo(() => {
      if (isRouteId) {
        return buildRouteUrl(to);
      }
      return to;
    }, [to, isRouteId, buildRouteUrl]);

    // Check if this is the active route
    const isActiveRoute = useIsActiveRoute(isRouteId ? to : '');
    const isActive = active !== undefined ? active : isActiveRoute;

    // Determine link behavior
    const shouldUseNextLink = !isExternalLink && (isRouteId ? isSameDomain(to) : true);
    const linkTarget = target || (isExternalLink ? '_blank' : '_self');
    const rel = isExternalLink ? 'noopener noreferrer' : undefined;

    // Handle validation in development
    if (process.env.NODE_ENV === 'development' && isRouteId && href === '#') {
      console.warn(`[CortexLink] Invalid route ID: ${to}`);
    }

    const linkClassName = cn(
      'transition-colors duration-200',
      isActive && 'font-semibold',
      className
    );

    // Use Next.js Link for same-domain navigation
    if (shouldUseNextLink) {
      return (
        <Link
          ref={ref}
          href={href}
          className={linkClassName}
          target={linkTarget}
          rel={rel}
          prefetch={prefetch}
          onClick={onClick}
          {...props}
        >
          {children}
        </Link>
      );
    }

    // Use regular anchor for external or cross-domain links
    return (
      <a
        ref={ref}
        href={href}
        className={linkClassName}
        target={linkTarget}
        rel={rel}
        onClick={onClick}
        {...props}
      >
        {children}
      </a>
    );
  }
);

CortexLink.displayName = 'CortexLink';
