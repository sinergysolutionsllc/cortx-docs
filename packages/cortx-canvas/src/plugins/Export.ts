import { toPng, toJpeg, toSvg } from 'html-to-image'
import { getNodesBounds, getViewportForBounds } from 'reactflow'
import { CanvasNode, CanvasEdge, ExportFormat, ExportOptions } from '../types'

const IMAGE_WIDTH = 1920
const IMAGE_HEIGHT = 1080

/**
 * Export canvas to PNG
 */
export async function exportToPng(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<void> {
  const {
    quality = 1,
    backgroundColor = '#ffffff',
    padding = 20,
    width,
    height,
  } = options

  try {
    const dataUrl = await toPng(canvasElement, {
      backgroundColor,
      width: width || IMAGE_WIDTH,
      height: height || IMAGE_HEIGHT,
      quality,
      pixelRatio: 2,
      style: {
        padding: `${padding}px`,
      },
    })

    downloadImage(dataUrl, 'workflow.png')
  } catch (error) {
    console.error('Failed to export PNG:', error)
    throw error
  }
}

/**
 * Export canvas to JPEG
 */
export async function exportToJpeg(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<void> {
  const {
    quality = 0.95,
    backgroundColor = '#ffffff',
    padding = 20,
    width,
    height,
  } = options

  try {
    const dataUrl = await toJpeg(canvasElement, {
      backgroundColor,
      width: width || IMAGE_WIDTH,
      height: height || IMAGE_HEIGHT,
      quality,
      pixelRatio: 2,
      style: {
        padding: `${padding}px`,
      },
    })

    downloadImage(dataUrl, 'workflow.jpeg')
  } catch (error) {
    console.error('Failed to export JPEG:', error)
    throw error
  }
}

/**
 * Export canvas to SVG
 */
export async function exportToSvg(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<void> {
  const {
    backgroundColor = '#ffffff',
    padding = 20,
    width,
    height,
  } = options

  try {
    const dataUrl = await toSvg(canvasElement, {
      backgroundColor,
      width: width || IMAGE_WIDTH,
      height: height || IMAGE_HEIGHT,
      style: {
        padding: `${padding}px`,
      },
    })

    downloadImage(dataUrl, 'workflow.svg')
  } catch (error) {
    console.error('Failed to export SVG:', error)
    throw error
  }
}

/**
 * Export canvas to JSON
 */
export function exportToJson(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  metadata?: Record<string, any>
): void {
  const data = {
    version: '1.0',
    timestamp: new Date().toISOString(),
    metadata: metadata || {},
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: node.data,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle,
      label: edge.label,
    })),
  }

  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = 'workflow.json'
  link.click()

  URL.revokeObjectURL(url)
}

/**
 * Helper function to download image
 */
function downloadImage(dataUrl: string, filename: string): void {
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename
  link.click()
}

/**
 * Main export function that delegates to specific formats
 */
export async function exportCanvas(
  format: ExportFormat,
  canvasElement: HTMLElement,
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: ExportOptions = {}
): Promise<void> {
  switch (format) {
    case 'png':
      return exportToPng(canvasElement, options)
    case 'jpeg':
      return exportToJpeg(canvasElement, options)
    case 'svg':
      return exportToSvg(canvasElement, options)
    case 'json':
      return exportToJson(nodes, edges)
    default:
      throw new Error(`Unsupported export format: ${format}`)
  }
}

/**
 * Calculate optimal viewport to fit all nodes
 */
export function calculateViewportForNodes(
  nodes: CanvasNode[],
  width: number,
  height: number,
  padding: number = 20
): { x: number; y: number; zoom: number } {
  const bounds = getNodesBounds(nodes as any)
  const viewport = getViewportForBounds(
    bounds,
    width,
    height,
    0.1, // minZoom
    2,   // maxZoom
    padding / 100
  )

  return viewport
}
