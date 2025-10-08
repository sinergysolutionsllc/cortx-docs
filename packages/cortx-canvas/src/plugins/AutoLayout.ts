import dagre from 'dagre'
import ELK from 'elkjs/lib/elk.bundled'
import { CanvasNode, CanvasEdge } from '../types'

const elk = new ELK()

export interface LayoutOptions {
  direction?: 'TB' | 'LR' | 'BT' | 'RL'
  nodeSpacing?: number
  rankSpacing?: number
  algorithm?: 'dagre' | 'elk-layered' | 'elk-force'
}

/**
 * Apply Dagre layout algorithm
 */
export async function applyDagreLayout(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: LayoutOptions = {}
): Promise<CanvasNode[]> {
  const {
    direction = 'TB',
    nodeSpacing = 50,
    rankSpacing = 100,
  } = options

  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({
    rankdir: direction,
    nodesep: nodeSpacing,
    ranksep: rankSpacing,
    marginx: 20,
    marginy: 20,
  })

  // Add nodes to graph
  nodes.forEach((node) => {
    // Estimate node dimensions (can be customized)
    const width = 180
    const height = 80
    g.setNode(node.id, { width, height })
  })

  // Add edges to graph
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  // Calculate layout
  dagre.layout(g)

  // Apply new positions to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWithPosition.width / 2,
        y: nodeWithPosition.y - nodeWithPosition.height / 2,
      },
    }
  })

  return layoutedNodes
}

/**
 * Apply ELK layered layout algorithm
 */
export async function applyElkLayeredLayout(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: LayoutOptions = {}
): Promise<CanvasNode[]> {
  const {
    direction = 'RIGHT',
    nodeSpacing = 50,
    rankSpacing = 100,
  } = options

  const elkNodes = nodes.map((node) => ({
    id: node.id,
    width: 180,
    height: 80,
  }))

  const elkEdges = edges.map((edge) => ({
    id: edge.id,
    sources: [edge.source],
    targets: [edge.target],
  }))

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': direction,
      'elk.spacing.nodeNode': nodeSpacing.toString(),
      'elk.layered.spacing.nodeNodeBetweenLayers': rankSpacing.toString(),
      'elk.padding': '[top=20,left=20,bottom=20,right=20]',
    },
    children: elkNodes,
    edges: elkEdges,
  }

  const layout = await elk.layout(graph)

  // Apply new positions to nodes
  const layoutedNodes = nodes.map((node) => {
    const elkNode = layout.children?.find((n) => n.id === node.id)
    if (!elkNode) return node

    return {
      ...node,
      position: {
        x: elkNode.x || 0,
        y: elkNode.y || 0,
      },
    }
  })

  return layoutedNodes
}

/**
 * Apply ELK force-directed layout algorithm
 */
export async function applyElkForceLayout(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: LayoutOptions = {}
): Promise<CanvasNode[]> {
  const { nodeSpacing = 100 } = options

  const elkNodes = nodes.map((node) => ({
    id: node.id,
    width: 180,
    height: 80,
  }))

  const elkEdges = edges.map((edge) => ({
    id: edge.id,
    sources: [edge.source],
    targets: [edge.target],
  }))

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'force',
      'elk.spacing.nodeNode': nodeSpacing.toString(),
      'elk.padding': '[top=20,left=20,bottom=20,right=20]',
    },
    children: elkNodes,
    edges: elkEdges,
  }

  const layout = await elk.layout(graph)

  // Apply new positions to nodes
  const layoutedNodes = nodes.map((node) => {
    const elkNode = layout.children?.find((n) => n.id === node.id)
    if (!elkNode) return node

    return {
      ...node,
      position: {
        x: elkNode.x || 0,
        y: elkNode.y || 0,
      },
    }
  })

  return layoutedNodes
}

/**
 * Main auto-layout function that delegates to specific algorithms
 */
export async function autoLayout(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: LayoutOptions = {}
): Promise<CanvasNode[]> {
  const { algorithm = 'dagre' } = options

  switch (algorithm) {
    case 'dagre':
      return applyDagreLayout(nodes, edges, options)
    case 'elk-layered':
      return applyElkLayeredLayout(nodes, edges, options)
    case 'elk-force':
      return applyElkForceLayout(nodes, edges, options)
    default:
      return applyDagreLayout(nodes, edges, options)
  }
}
