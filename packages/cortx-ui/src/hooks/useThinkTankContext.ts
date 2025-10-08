"use client"

import { useMemo } from 'react'
import { usePathname } from 'next/navigation'
import type { ThinkTankContext } from '../components/thinktank/types'

/**
 * Hook to detect current suite/module context from URL
 *
 * Parses the pathname to extract suite_id and module_id for hierarchical RAG retrieval.
 *
 * URL patterns:
 * - /fedsuite/dataflow/... → { suite_id: 'fedsuite', module_id: 'dataflow' }
 * - /fedsuite/... → { suite_id: 'fedsuite', module_id: null }
 * - /thinktank → { suite_id: null, module_id: null }
 *
 * @param user_id - Optional user ID to include in context
 * @param user_role - Optional user role to include in context
 * @returns ThinkTankContext object with suite_id, module_id, and route
 */
export function useThinkTankContext(
  user_id?: string,
  user_role?: string
): ThinkTankContext {
  const pathname = usePathname()

  const context = useMemo(() => {
    const parts = pathname.split('/').filter(Boolean)

    // Known suite IDs
    const SUITES = ['fedsuite', 'corpsuite', 'medsuite', 'govsuite']

    // Extract suite_id (first path segment if it's a known suite)
    const suite_id = parts.length > 0 && SUITES.includes(parts[0]) ? parts[0] : null

    // Extract module_id (second path segment if suite is present)
    const module_id = suite_id && parts.length > 1 ? parts[1] : null

    return {
      suite_id,
      module_id,
      entity_id: null, // Can be set by caller if tenant context is available
      route: pathname,
      user_id,
      user_role
    }
  }, [pathname, user_id, user_role])

  return context
}

/**
 * Hook to check if current page is the ThinkTank full page
 */
export function useIsThinkTankPage(): boolean {
  const pathname = usePathname()
  return pathname === '/thinktank'
}
