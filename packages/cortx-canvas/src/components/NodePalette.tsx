'use client'

import { useState, useMemo } from 'react'
import { Search, ChevronDown, ChevronRight, Plus } from 'lucide-react'
import { useNodeRegistry } from '../hooks/useNodeRegistry'
import { NodeCategory, NodePaletteConfig } from '../types'
import { cn } from '../utils/cn'

interface NodePaletteProps {
  config?: NodePaletteConfig
  onNodeAdd?: (nodeType: string) => void
  className?: string
}

export function NodePalette({
  config = {},
  onNodeAdd,
  className,
}: NodePaletteProps) {
  const {
    searchable = true,
    collapsible = true,
    defaultExpanded = true,
    showIcons = true,
    groupByCategory = true,
  } = config

  const [searchQuery, setSearchQuery] = useState('')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    defaultExpanded ? new Set(['all']) : new Set()
  )

  const definitions = useNodeRegistry((state) => state.getAll())
  const searchNodes = useNodeRegistry((state) => state.search)

  // Get categories
  const categories = useMemo(() => {
    const catMap = new Map<string, NodeCategory>()

    definitions.forEach((def) => {
      if (!catMap.has(def.category)) {
        catMap.set(def.category, {
          id: def.category,
          label: def.category,
          color: def.color,
        })
      }
    })

    return Array.from(catMap.values()).sort((a, b) =>
      a.label.localeCompare(b.label)
    )
  }, [definitions])

  // Filter nodes based on search
  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) {
      return definitions
    }
    return searchNodes(searchQuery)
  }, [searchQuery, definitions, searchNodes])

  // Group nodes by category
  const nodesByCategory = useMemo(() => {
    const grouped = new Map<string, typeof definitions>()

    filteredNodes.forEach((node) => {
      const cat = node.category
      if (!grouped.has(cat)) {
        grouped.set(cat, [])
      }
      grouped.get(cat)!.push(node)
    })

    return grouped
  }, [filteredNodes])

  const toggleCategory = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId)
    } else {
      newExpanded.add(categoryId)
    }
    setExpandedCategories(newExpanded)
  }

  const handleDragStart = (
    event: React.DragEvent<HTMLDivElement>,
    nodeType: string
  ) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div
      className={cn(
        'flex h-full w-64 flex-col border-r border-slate-200 bg-white shadow-sm',
        className
      )}
    >
      {/* Header */}
      <div className="border-b border-slate-200 p-4">
        <h3 className="text-sm font-semibold text-slate-800">Node Palette</h3>
        <p className="text-xs text-slate-500">Drag nodes to canvas</p>
      </div>

      {/* Search */}
      {searchable && (
        <div className="border-b border-slate-200 p-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-800 placeholder-slate-400 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
            />
          </div>
        </div>
      )}

      {/* Node list */}
      <div className="flex-1 overflow-y-auto p-2">
        {groupByCategory ? (
          // Grouped by category
          categories.map((category) => {
            const nodes = nodesByCategory.get(category.id) || []
            if (nodes.length === 0) return null

            const isExpanded = expandedCategories.has(category.id)

            return (
              <div key={category.id} className="mb-2">
                {/* Category header */}
                <button
                  onClick={() => collapsible && toggleCategory(category.id)}
                  className="mb-1 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors hover:bg-slate-100"
                >
                  {collapsible &&
                    (isExpanded ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    ))}
                  <span>{category.label}</span>
                  <span className="ml-auto text-slate-400">{nodes.length}</span>
                </button>

                {/* Nodes */}
                {isExpanded && (
                  <div className="space-y-1">
                    {nodes.map((node) => {
                      const Icon = node.icon
                      return (
                        <div
                          key={node.type}
                          draggable
                          onDragStart={(e) => handleDragStart(e, node.type)}
                          onClick={() => onNodeAdd?.(node.type)}
                          className="group flex cursor-grab items-center gap-2 rounded-lg border border-transparent bg-white p-2 transition-all hover:border-slate-200 hover:bg-slate-50 hover:shadow-sm active:cursor-grabbing"
                          title={node.description}
                        >
                          {showIcons && (
                            <div
                              className={cn(
                                'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md shadow-sm transition-transform group-hover:scale-110',
                                node.color
                              )}
                            >
                              <Icon className="h-4 w-4 text-white" />
                            </div>
                          )}

                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-medium text-slate-800">
                              {node.label}
                            </div>
                            {node.description && (
                              <div className="truncate text-xs text-slate-500">
                                {node.description}
                              </div>
                            )}
                          </div>

                          <Plus className="h-4 w-4 flex-shrink-0 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })
        ) : (
          // Flat list
          <div className="space-y-1">
            {filteredNodes.map((node) => {
              const Icon = node.icon
              return (
                <div
                  key={node.type}
                  draggable
                  onDragStart={(e) => handleDragStart(e, node.type)}
                  onClick={() => onNodeAdd?.(node.type)}
                  className="group flex cursor-grab items-center gap-2 rounded-lg border border-transparent bg-white p-2 transition-all hover:border-slate-200 hover:bg-slate-50 hover:shadow-sm active:cursor-grabbing"
                  title={node.description}
                >
                  {showIcons && (
                    <div
                      className={cn(
                        'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md shadow-sm transition-transform group-hover:scale-110',
                        node.color
                      )}
                    >
                      <Icon className="h-4 w-4 text-white" />
                    </div>
                  )}

                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-slate-800">
                      {node.label}
                    </div>
                    {node.description && (
                      <div className="truncate text-xs text-slate-500">
                        {node.description}
                      </div>
                    )}
                  </div>

                  <Plus className="h-4 w-4 flex-shrink-0 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
              )
            })}
          </div>
        )}

        {filteredNodes.length === 0 && (
          <div className="flex h-32 items-center justify-center text-sm text-slate-400">
            No nodes found
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 p-3 text-xs text-slate-500">
        {filteredNodes.length} node{filteredNodes.length !== 1 ? 's' : ''} available
      </div>
    </div>
  )
}
