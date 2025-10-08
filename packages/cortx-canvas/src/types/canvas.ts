import { Node as ReactFlowNode, Edge as ReactFlowEdge } from 'reactflow'

export interface CanvasNode extends ReactFlowNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: NodeData
}

export interface NodeData {
  label: string
  nodeType: string
  description?: string
  status?: 'idle' | 'running' | 'completed' | 'error' | 'warning'
  recordCount?: number
  processingTime?: number
  isConfigured?: boolean
  properties?: Record<string, any>
  [key: string]: any
}

export interface CanvasEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  label?: string
  animated?: boolean
  style?: React.CSSProperties
  markerEnd?: string
}

export interface CanvasState {
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  selectedNodes: string[]
  selectedEdges: string[]
  viewport: { x: number; y: number; zoom: number }
}

export interface CanvasConfig {
  snapToGrid?: boolean
  gridSize?: number
  minZoom?: number
  maxZoom?: number
  defaultEdgeOptions?: Partial<CanvasEdge>
  fitViewOnInit?: boolean
  connectionMode?: 'strict' | 'loose'
  multiSelectionKeyCode?: string
  selectionMode?: 'full' | 'partial'
}

export interface CanvasCallbacks {
  onNodesChange?: (nodes: CanvasNode[]) => void
  onEdgesChange?: (edges: CanvasEdge[]) => void
  onNodeClick?: (node: CanvasNode) => void
  onNodeDoubleClick?: (node: CanvasNode) => void
  onNodeContextMenu?: (event: React.MouseEvent, node: CanvasNode) => void
  onEdgeClick?: (edge: CanvasEdge) => void
  onConnect?: (connection: { source: string; target: string; sourceHandle?: string; targetHandle?: string }) => void
  onSelectionChange?: (nodes: CanvasNode[], edges: CanvasEdge[]) => void
  onPaneClick?: () => void
  onNodeDragStop?: (event: React.MouseEvent, node: CanvasNode) => void
}

export interface LayoutAlgorithm {
  name: string
  label: string
  description: string
  options?: Record<string, any>
}

export type ExportFormat = 'png' | 'svg' | 'jpeg' | 'json'

export interface ExportOptions {
  format?: ExportFormat
  quality?: number // 0-1 for jpeg
  backgroundColor?: string
  padding?: number
  width?: number
  height?: number
}
