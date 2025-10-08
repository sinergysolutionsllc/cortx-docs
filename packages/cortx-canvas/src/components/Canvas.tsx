'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  useReactFlow,
  Connection,
  Edge,
  Node as ReactFlowNode,
  ReactFlowInstance,
  BackgroundVariant,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { Node } from './Node'
import { CanvasNode, CanvasEdge, CanvasConfig, CanvasCallbacks } from '../types'
import { useCanvasHistory } from '../hooks/useCanvasHistory'
import { cn } from '../utils/cn'

// Memoize nodeTypes to prevent ReactFlow warnings
const nodeTypes = {
  custom: Node,
}

interface CanvasProps {
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  config?: CanvasConfig
  callbacks?: CanvasCallbacks
  className?: string
  showMinimap?: boolean
  showControls?: boolean
  showBackground?: boolean
  backgroundVariant?: BackgroundVariant
  children?: React.ReactNode
}

function CanvasInner({
  nodes: initialNodes,
  edges: initialEdges,
  config = {},
  callbacks = {},
  className,
  showMinimap = true,
  showControls = true,
  showBackground = true,
  backgroundVariant = BackgroundVariant.Dots,
  children,
}: CanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null)
  const { fitView } = useReactFlow()
  const pushHistory = useCanvasHistory((state) => state.pushHistory)

  const {
    snapToGrid = true,
    gridSize = 15,
    minZoom = 0.1,
    maxZoom = 4,
    fitViewOnInit = true,
    connectionMode = 'loose',
    multiSelectionKeyCode = 'Shift',
    selectionMode = 'partial',
    defaultEdgeOptions = {
      type: 'smoothstep',
      animated: false,
      style: { stroke: '#2D5972', strokeWidth: 2 },
      markerEnd: 'arrowclosed' as any,
    },
  } = config

  // Convert to ReactFlow format
  const convertedNodes: ReactFlowNode[] = initialNodes.map((node) => ({
    id: node.id,
    type: 'custom',
    position: node.position,
    data: node.data,
  }))

  const convertedEdges: Edge[] = initialEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle,
    targetHandle: edge.targetHandle,
    label: edge.label,
    animated: edge.animated,
    style: edge.style || defaultEdgeOptions.style,
    markerEnd: (edge.markerEnd || defaultEdgeOptions.markerEnd) as any,
    className: cn(
      'transition-all duration-300',
      edge.animated && 'animate-pulse'
    ),
    labelBgStyle: {
      fill: '#E5FCFF',
      color: '#2D5972',
      fontSize: 12,
      fontWeight: 500,
    },
    labelStyle: {
      fill: '#2D5972',
      fontSize: 12,
      fontWeight: 500,
    },
  }) as Edge)

  const [nodes, setNodes, onNodesChange] = useNodesState(convertedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(convertedEdges)

  // Track the last state we sent to parent to prevent circular updates
  const lastSentNodesRef = useRef<string>('')
  const lastSentEdgesRef = useRef<string>('')

  // Sync external state changes to internal state (only if they came from outside, not from us)
  useEffect(() => {
    const nodesJson = JSON.stringify(
      initialNodes.map(n => ({
        id: n.id,
        position: n.position,
        data: Object.fromEntries(
          Object.entries(n.data).filter(([_, value]) => typeof value !== 'function')
        )
      }))
    )

    // Only sync if the incoming nodes are different from what we last sent to parent
    if (nodesJson !== lastSentNodesRef.current) {
      const newNodes = initialNodes.map((node) => ({
        id: node.id,
        type: 'custom',
        position: node.position,
        data: node.data,
      }))
      setNodes(newNodes)
    }
  }, [initialNodes, setNodes])

  useEffect(() => {
    const edgesJson = JSON.stringify(initialEdges)

    // Only sync if the incoming edges are different from what we last sent to parent
    if (edgesJson !== lastSentEdgesRef.current) {
      const newEdges = initialEdges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
        label: edge.label,
        animated: edge.animated,
        style: edge.style || defaultEdgeOptions.style,
        markerEnd: (edge.markerEnd || defaultEdgeOptions.markerEnd) as any,
      }) as Edge)
      setEdges(newEdges)
    }
  }, [initialEdges, setEdges, defaultEdgeOptions])

  // Fit view on init
  useEffect(() => {
    if (fitViewOnInit && reactFlowInstance && nodes.length > 0) {
      setTimeout(() => fitView({ padding: 0.2, duration: 800 }), 100)
    }
  }, [fitViewOnInit, reactFlowInstance, nodes.length, fitView])

  // Handle connections
  const onConnect = useCallback(
    (connection: Connection) => {
      const newEdge: Edge = {
        ...connection,
        id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
        ...defaultEdgeOptions,
      } as Edge

      setEdges((eds) => addEdge(newEdge, eds))

      if (callbacks.onConnect) {
        callbacks.onConnect({
          source: connection.source!,
          target: connection.target!,
          sourceHandle: connection.sourceHandle || undefined,
          targetHandle: connection.targetHandle || undefined,
        })
      }

      // Push to history
      pushHistory(
        nodes as CanvasNode[],
        [...edges, newEdge as CanvasEdge] as CanvasEdge[]
      )
    },
    [setEdges, callbacks, defaultEdgeOptions, pushHistory, nodes, edges]
  )

  // Handle node click
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: ReactFlowNode) => {
      if (callbacks.onNodeClick) {
        callbacks.onNodeClick(node as CanvasNode)
      }
    },
    [callbacks]
  )

  // Handle node double click
  const onNodeDoubleClick = useCallback(
    (_event: React.MouseEvent, node: ReactFlowNode) => {
      if (callbacks.onNodeDoubleClick) {
        callbacks.onNodeDoubleClick(node as CanvasNode)
      }
    },
    [callbacks]
  )

  // Handle edge click
  const onEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      if (callbacks.onEdgeClick) {
        callbacks.onEdgeClick(edge as CanvasEdge)
      }
    },
    [callbacks]
  )

  // Handle pane click
  const onPaneClick = useCallback(() => {
    if (callbacks.onPaneClick) {
      callbacks.onPaneClick()
    }
  }, [callbacks])

  // Handle selection change
  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: { nodes: ReactFlowNode[]; edges: Edge[] }) => {
      if (callbacks.onSelectionChange) {
        callbacks.onSelectionChange(selectedNodes as CanvasNode[], selectedEdges as CanvasEdge[])
      }
    },
    [callbacks]
  )

  // Handle drag stop
  const onNodeDragStop = useCallback(
    (event: React.MouseEvent, node: ReactFlowNode) => {
      if (callbacks.onNodeDragStop) {
        callbacks.onNodeDragStop(event, node as CanvasNode)
      }
      pushHistory(nodes as CanvasNode[], edges as CanvasEdge[])
    },
    [callbacks, pushHistory, nodes, edges]
  )

  // Wrap change handlers to notify parent and track what we sent
  const handleNodesChange = useCallback((changes: any) => {
    onNodesChange(changes)
  }, [onNodesChange])

  const handleEdgesChange = useCallback((changes: any) => {
    onEdgesChange(changes)
  }, [onEdgesChange])

  // Notify parent when internal state changes (after ReactFlow applies changes)
  useEffect(() => {
    if (callbacks.onNodesChange) {
      const convertedNodes = nodes.map(node => ({
        id: node.id,
        type: node.data.nodeType,
        position: node.position,
        data: node.data,
      } as CanvasNode))

      const nodesJson = JSON.stringify(
        convertedNodes.map(n => ({
          id: n.id,
          position: n.position,
          data: Object.fromEntries(
            Object.entries(n.data).filter(([_, value]) => typeof value !== 'function')
          )
        }))
      )

      // Update ref before calling callback to prevent circular updates
      lastSentNodesRef.current = nodesJson
      callbacks.onNodesChange(convertedNodes)
    }
  }, [nodes, callbacks])

  useEffect(() => {
    if (callbacks.onEdgesChange) {
      const convertedEdges = edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
        label: edge.label,
        animated: edge.animated,
        style: edge.style,
        markerEnd: edge.markerEnd,
      } as CanvasEdge))

      const edgesJson = JSON.stringify(convertedEdges)

      // Update ref before calling callback to prevent circular updates
      lastSentEdgesRef.current = edgesJson
      callbacks.onEdgesChange(convertedEdges)
    }
  }, [edges, callbacks])

  return (
    <div ref={reactFlowWrapper} className={cn('h-full w-full', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onSelectionChange={onSelectionChange}
        onNodeDragStop={onNodeDragStop}
        onInit={setReactFlowInstance}
        nodeTypes={nodeTypes}
        snapToGrid={snapToGrid}
        snapGrid={[gridSize, gridSize]}
        minZoom={minZoom}
        maxZoom={maxZoom}
        defaultEdgeOptions={defaultEdgeOptions}
        connectionMode={connectionMode as any}
        multiSelectionKeyCode={multiSelectionKeyCode as any}
        selectionMode={selectionMode as any}
        fitView={fitViewOnInit}
        attributionPosition="bottom-right"
        className="bg-gradient-to-br from-slate-50 to-slate-100"
      >
        {showBackground && (
          <Background
            variant={backgroundVariant}
            gap={gridSize}
            size={1}
            color="#cbd5e1"
            className="opacity-50"
          />
        )}

        {showControls && (
          <Controls
            className="rounded-lg border border-slate-300 bg-white shadow-lg"
            showInteractive={false}
          />
        )}

        {showMinimap && (
          <MiniMap
            className="rounded-lg border border-slate-300 bg-white shadow-lg"
            nodeColor={(node) => {
              const nodeDef = node.data?.nodeType
              return nodeDef ? '#00C2CB' : '#94a3b8'
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
            pannable
            zoomable
          />
        )}

        {children && <Panel position="top-left">{children}</Panel>}
      </ReactFlow>
    </div>
  )
}

export function Canvas(props: CanvasProps) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  )
}
