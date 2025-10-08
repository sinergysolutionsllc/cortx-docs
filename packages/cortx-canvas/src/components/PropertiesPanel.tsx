'use client'

import { X } from 'lucide-react'
import { CanvasNode } from '../types'
import { useNodeRegistry } from '../hooks/useNodeRegistry'
import { cn } from '../utils/cn'

interface PropertiesPanelProps {
  node: CanvasNode | null
  onClose: () => void
  onUpdate: (nodeId: string, data: Record<string, any>) => void
  className?: string
}

export function PropertiesPanel({
  node,
  onClose,
  onUpdate,
  className,
}: PropertiesPanelProps) {
  if (!node) return null

  const nodeDef = useNodeRegistry((state) => state.get(node.data.nodeType))

  const handlePropertyChange = (key: string, value: any) => {
    onUpdate(node.id, {
      ...node.data,
      properties: {
        ...node.data.properties,
        [key]: value,
      },
    })
  }

  const handleLabelChange = (value: string) => {
    onUpdate(node.id, {
      ...node.data,
      label: value,
    })
  }

  const handleDescriptionChange = (value: string) => {
    onUpdate(node.id, {
      ...node.data,
      description: value,
    })
  }

  return (
    <div
      className={cn(
        'flex h-full w-80 flex-col border-l border-slate-200 bg-white shadow-lg',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 p-4">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-slate-800">
            Node Properties
          </h3>
          {nodeDef && (
            <p className="truncate text-xs text-slate-500">{nodeDef.label}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="ml-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          title="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {/* Basic Properties */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-600">
              Node ID
            </label>
            <input
              type="text"
              value={node.id}
              disabled
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-600">
              Label
            </label>
            <input
              type="text"
              value={node.data.label}
              onChange={(e) => handleLabelChange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
              placeholder="Enter node label"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-600">
              Description
            </label>
            <textarea
              value={node.data.description || ''}
              onChange={(e) => handleDescriptionChange(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
              placeholder="Enter node description"
            />
          </div>

          {/* Custom Properties based on node type */}
          {nodeDef?.properties && nodeDef.properties.length > 0 && (
            <>
              <div className="border-t border-slate-200 pt-4">
                <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  {nodeDef.label} Properties
                </h4>
              </div>

              {nodeDef.properties.map((prop) => {
                const currentValue = node.data.properties?.[prop.key] ?? prop.default

                return (
                  <div key={prop.key}>
                    <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-600">
                      {prop.label}
                      {prop.required && (
                        <span className="ml-1 text-red-500">*</span>
                      )}
                    </label>

                    {prop.type === 'text' && (
                      <input
                        type="text"
                        value={currentValue || ''}
                        onChange={(e) =>
                          handlePropertyChange(prop.key, e.target.value)
                        }
                        placeholder={prop.placeholder}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
                      />
                    )}

                    {prop.type === 'number' && (
                      <input
                        type="number"
                        value={currentValue || ''}
                        onChange={(e) =>
                          handlePropertyChange(prop.key, parseFloat(e.target.value))
                        }
                        min={prop.min}
                        max={prop.max}
                        placeholder={prop.placeholder}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
                      />
                    )}

                    {prop.type === 'boolean' && (
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={currentValue || false}
                          onChange={(e) =>
                            handlePropertyChange(prop.key, e.target.checked)
                          }
                          className="h-4 w-4 rounded border-slate-300 text-sinergy-teal focus:ring-sinergy-teal"
                        />
                        <span className="text-sm text-slate-700">
                          {prop.description || 'Enable'}
                        </span>
                      </label>
                    )}

                    {prop.type === 'select' && prop.options && (
                      <select
                        value={currentValue || ''}
                        onChange={(e) =>
                          handlePropertyChange(prop.key, e.target.value)
                        }
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
                      >
                        <option value="">Select {prop.label}</option>
                        {prop.options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    )}

                    {prop.type === 'textarea' && (
                      <textarea
                        value={currentValue || ''}
                        onChange={(e) =>
                          handlePropertyChange(prop.key, e.target.value)
                        }
                        rows={4}
                        placeholder={prop.placeholder}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
                      />
                    )}

                    {prop.type === 'json' && (
                      <textarea
                        value={
                          typeof currentValue === 'object'
                            ? JSON.stringify(currentValue, null, 2)
                            : currentValue || ''
                        }
                        onChange={(e) => {
                          try {
                            const parsed = JSON.parse(e.target.value)
                            handlePropertyChange(prop.key, parsed)
                          } catch {
                            // Invalid JSON, keep as string
                            handlePropertyChange(prop.key, e.target.value)
                          }
                        }}
                        rows={6}
                        placeholder={prop.placeholder}
                        className="font-mono w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 transition-all focus:border-sinergy-teal focus:outline-none focus:ring-2 focus:ring-sinergy-teal/20"
                      />
                    )}

                    {prop.description && (
                      <p className="mt-1 text-xs text-slate-500">
                        {prop.description}
                      </p>
                    )}
                  </div>
                )
              })}
            </>
          )}

          {/* Node Info */}
          <div className="border-t border-slate-200 pt-4">
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-600">
              Node Information
            </h4>
            <dl className="space-y-2 text-xs">
              <div className="flex justify-between">
                <dt className="text-slate-600">Type:</dt>
                <dd className="font-medium text-slate-800">
                  {node.data.nodeType}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">Category:</dt>
                <dd className="font-medium text-slate-800">
                  {nodeDef?.category || 'Unknown'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">Position:</dt>
                <dd className="font-medium text-slate-800">
                  ({Math.round(node.position.x)}, {Math.round(node.position.y)})
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
