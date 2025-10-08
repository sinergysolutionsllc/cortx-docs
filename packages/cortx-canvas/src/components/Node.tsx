'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { X, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react'
import { cn } from '../utils/cn'
import { NodeData } from '../types'
import { useNodeRegistry } from '../hooks/useNodeRegistry'

export interface EnhancedNodeProps extends NodeProps {
  data: NodeData & {
    onDelete?: () => void
  }
}

export const Node = memo(({ data, selected, id }: EnhancedNodeProps) => {
  const nodeDef = useNodeRegistry((state) => state.get(data.nodeType))

  if (!nodeDef) {
    return (
      <div className="rounded-lg border-2 border-red-400 bg-red-50 p-4 text-red-800 shadow-lg">
        <div className="text-sm font-semibold">Unknown node type</div>
        <div className="text-xs">{data.nodeType}</div>
      </div>
    )
  }

  const Icon = nodeDef.icon

  const getStatusStyles = () => {
    switch (data.status) {
      case 'running':
        return 'border-blue-500 bg-gradient-to-br from-blue-50 to-blue-100 shadow-blue-200'
      case 'completed':
        return 'border-green-500 bg-gradient-to-br from-green-50 to-green-100 shadow-green-200'
      case 'error':
        return 'border-red-500 bg-gradient-to-br from-red-50 to-red-100 shadow-red-200'
      case 'warning':
        return 'border-yellow-500 bg-gradient-to-br from-yellow-50 to-yellow-100 shadow-yellow-200'
      default:
        return 'border-slate-300 bg-gradient-to-br from-white to-slate-50 shadow-slate-200 hover:shadow-slate-300'
    }
  }

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running':
        return <Clock className="h-3.5 w-3.5 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="h-3.5 w-3.5 text-green-600" />
      case 'error':
        return <AlertCircle className="h-3.5 w-3.5 text-red-600" />
      case 'warning':
        return <AlertCircle className="h-3.5 w-3.5 text-yellow-600" />
      default:
        return null
    }
  }

  const baseClasses = cn(
    'group relative min-w-[160px] rounded-xl border-2 px-4 py-3.5 shadow-lg transition-all duration-300',
    getStatusStyles(),
    selected && 'scale-105 ring-4 ring-sinergy-teal/50 ring-offset-2 shadow-2xl',
    !data.isConfigured && 'border-red-400 ring-2 ring-red-200',
    'hover:scale-[1.02] hover:shadow-xl'
  )

  return (
    <div className="relative">
      {/* Delete button */}
      {data.onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            data.onDelete?.()
          }}
          className="absolute -right-2 -top-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white opacity-0 shadow-lg transition-all duration-200 hover:bg-red-600 hover:scale-110 group-hover:opacity-100"
          title="Delete node"
        >
          <X className="h-3 w-3" />
        </button>
      )}

      {/* Status indicator badge */}
      {data.status && data.status !== 'idle' && (
        <div className="absolute -top-2 left-1/2 z-10 flex -translate-x-1/2 items-center gap-1 rounded-full bg-white px-2 py-1 shadow-md ring-1 ring-slate-200">
          {getStatusIcon()}
        </div>
      )}

      {/* Special indicator (AI-generated, CORTX-specific, etc.) */}
      {nodeDef.tags?.includes('cortx') && (
        <div className="absolute -left-2 -top-2 z-10 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-gradient-to-br from-sinergy-teal to-teal-400 shadow-lg">
          <Zap className="h-3 w-3 text-white" />
        </div>
      )}

      {/* Main node content */}
      <div className={baseClasses}>
        <div className="flex items-center gap-3">
          {/* Icon with gradient background */}
          <div
            className={cn(
              'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg shadow-sm transition-transform duration-300 group-hover:scale-110',
              nodeDef.color
            )}
          >
            <Icon className="h-5 w-5 text-white drop-shadow" />
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold text-slate-800">
              {data.label}
            </div>
            <div className="truncate text-xs font-medium capitalize text-slate-500">
              {nodeDef.label}
            </div>
          </div>
        </div>

        {/* Description */}
        {data.description && (
          <div className="mt-2 border-t border-slate-200 pt-2 text-xs text-slate-600">
            {data.description}
          </div>
        )}
      </div>

      {/* Metrics overlay */}
      {(data.recordCount !== undefined || data.processingTime !== undefined) && (
        <div className="absolute -bottom-6 left-0 right-0 rounded-lg border border-slate-200 bg-white px-2 py-1 text-center text-xs text-slate-600 shadow-sm">
          {data.recordCount !== undefined && (
            <span className="font-medium">{data.recordCount.toLocaleString()} records</span>
          )}
          {data.recordCount !== undefined && data.processingTime !== undefined && (
            <span className="mx-1 text-slate-400">•</span>
          )}
          {data.processingTime !== undefined && (
            <span className="font-medium">{data.processingTime}ms</span>
          )}
        </div>
      )}

      {/* Input handle */}
      {nodeDef.ports.input && (
        <Handle
          type="target"
          position={Position.Left}
          className="h-3 w-3 border-2 border-white bg-sinergy-teal shadow-md transition-all hover:scale-125"
          style={{ left: -6 }}
          isConnectable={true}
        />
      )}

      {/* Output handles */}
      {nodeDef.ports.output && !nodeDef.ports.multipleOutputs && (
        <Handle
          type="source"
          position={Position.Right}
          className="h-3 w-3 border-2 border-white bg-sinergy-teal shadow-md transition-all hover:scale-125"
          style={{ right: -6 }}
          isConnectable={true}
        />
      )}

      {/* Multiple output handles with labels */}
      {nodeDef.ports.multipleOutputs && nodeDef.ports.outputLabels && (
        <>
          {nodeDef.ports.outputLabels.map((label, index) => {
            const total = nodeDef.ports.outputLabels!.length
            const spacing = 100 / (total + 1)
            const topPercent = spacing * (index + 1)

            const handleColor =
              label.toLowerCase() === 'pass' ||
              label.toLowerCase() === 'true' ||
              label.toLowerCase() === 'approved'
                ? 'bg-green-500'
                : label.toLowerCase() === 'fail' ||
                  label.toLowerCase() === 'false' ||
                  label.toLowerCase() === 'rejected'
                ? 'bg-red-500'
                : label.toLowerCase() === 'warning' || label.toLowerCase() === 'override'
                ? 'bg-yellow-500'
                : 'bg-sinergy-teal'

            return (
              <Handle
                key={label}
                type="source"
                position={Position.Right}
                id={label.toLowerCase()}
                className={cn(
                  'h-3 w-3 border-2 border-white shadow-md transition-all hover:scale-125',
                  handleColor
                )}
                style={{
                  right: -6,
                  top: `${topPercent}%`,
                  transform: 'translateY(-50%)',
                }}
                isConnectable={true}
              />
            )
          })}

          {/* Handle labels */}
          <div className="absolute -right-20 top-0 bottom-0 flex flex-col justify-center gap-2">
            {nodeDef.ports.outputLabels.map((label) => (
              <div
                key={label}
                className="rounded bg-white px-2 py-0.5 text-xs font-medium text-slate-600 shadow-sm ring-1 ring-slate-200"
              >
                {label}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
})

Node.displayName = 'Node'
