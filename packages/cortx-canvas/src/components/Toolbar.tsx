'use client'

import { Download, Undo2, Redo2, ZoomIn, ZoomOut, Maximize2, Save, Grid3x3, Layout, CheckCircle2 } from 'lucide-react'
import { useReactFlow } from 'reactflow'
import { useCanvasHistory } from '../hooks/useCanvasHistory'
import { ExportFormat } from '../types'
import { cn } from '../utils/cn'

interface ToolbarProps {
  onSave?: () => void
  onCompile?: () => void
  onExport?: (format: ExportFormat) => void
  onAutoLayout?: () => void
  onUndo?: () => void
  onRedo?: () => void
  showSave?: boolean
  showCompile?: boolean
  showExport?: boolean
  showAutoLayout?: boolean
  showZoom?: boolean
  showFitView?: boolean
  className?: string
}

export function Toolbar({
  onSave,
  onCompile,
  onExport,
  onAutoLayout,
  onUndo,
  onRedo,
  showSave = true,
  showCompile = false,
  showExport = true,
  showAutoLayout = true,
  showZoom = true,
  showFitView = true,
  className,
}: ToolbarProps) {
  const { zoomIn, zoomOut, fitView } = useReactFlow()
  const canUndo = useCanvasHistory((state) => state.canUndo())
  const canRedo = useCanvasHistory((state) => state.canRedo())

  const handleUndo = () => {
    if (onUndo) {
      onUndo()
    }
  }

  const handleRedo = () => {
    if (onRedo) {
      onRedo()
    }
  }

  return (
    <div
      className={cn(
        'flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1 shadow-lg',
        className
      )}
    >
      {/* Undo/Redo */}
      <div className="flex gap-0.5 border-r border-slate-200 pr-1">
        <button
          onClick={handleUndo}
          disabled={!canUndo}
          className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
          title="Undo (Ctrl+Z)"
        >
          <Undo2 className="h-4 w-4" />
        </button>
        <button
          onClick={handleRedo}
          disabled={!canRedo}
          className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
          title="Redo (Ctrl+Y)"
        >
          <Redo2 className="h-4 w-4" />
        </button>
      </div>

      {/* Zoom controls */}
      {showZoom && (
        <div className="flex gap-0.5 border-r border-slate-200 pr-1">
          <button
            onClick={() => zoomIn({ duration: 300 })}
            className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900"
            title="Zoom In (+)"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={() => zoomOut({ duration: 300 })}
            className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900"
            title="Zoom Out (-)"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Fit view */}
      {showFitView && (
        <div className="flex gap-0.5 border-r border-slate-200 pr-1">
          <button
            onClick={() => fitView({ padding: 0.2, duration: 300 })}
            className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900"
            title="Fit View (Ctrl+0)"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Auto Layout */}
      {showAutoLayout && onAutoLayout && (
        <div className="flex gap-0.5 border-r border-slate-200 pr-1">
          <button
            onClick={onAutoLayout}
            className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900"
            title="Auto Layout"
          >
            <Layout className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Export */}
      {showExport && onExport && (
        <div className="flex gap-0.5 border-r border-slate-200 pr-1">
          <div className="relative group">
            <button
              className="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 transition-all hover:bg-slate-100 hover:text-slate-900"
              title="Export"
            >
              <Download className="h-4 w-4" />
            </button>

            {/* Export dropdown */}
            <div className="absolute left-0 top-full z-10 mt-1 hidden min-w-[120px] rounded-lg border border-slate-200 bg-white py-1 shadow-xl group-hover:block">
              <button
                onClick={() => onExport('png')}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-100"
              >
                Export PNG
              </button>
              <button
                onClick={() => onExport('svg')}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-100"
              >
                Export SVG
              </button>
              <button
                onClick={() => onExport('jpeg')}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-100"
              >
                Export JPEG
              </button>
              <button
                onClick={() => onExport('json')}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-100"
              >
                Export JSON
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Compile */}
      {showCompile && onCompile && (
        <button
          onClick={onCompile}
          className="flex h-8 items-center gap-1.5 rounded-md bg-sinergy-navy px-3 text-sm font-medium text-white transition-all hover:bg-sinergy-navy/90 hover:shadow-md"
          title="Compile Workflow"
        >
          <CheckCircle2 className="h-4 w-4" />
          Compile
        </button>
      )}

      {/* Save */}
      {showSave && onSave && (
        <button
          onClick={onSave}
          className="flex h-8 items-center gap-1.5 rounded-md bg-sinergy-teal px-3 text-sm font-medium text-white transition-all hover:bg-sinergy-teal/90 hover:shadow-md"
          title="Save (Ctrl+S)"
        >
          <Save className="h-4 w-4" />
          Save
        </button>
      )}
    </div>
  )
}
