import { create } from 'zustand'
import { CanvasNode, CanvasEdge } from '../types'

interface HistoryEntry {
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  timestamp: number
}

interface CanvasHistoryStore {
  past: HistoryEntry[]
  future: HistoryEntry[]
  maxHistorySize: number

  pushHistory: (nodes: CanvasNode[], edges: CanvasEdge[]) => void
  undo: () => { nodes: CanvasNode[]; edges: CanvasEdge[] } | null
  redo: () => { nodes: CanvasNode[]; edges: CanvasEdge[] } | null
  canUndo: () => boolean
  canRedo: () => boolean
  clear: () => void
}

export const useCanvasHistory = create<CanvasHistoryStore>((set, get) => ({
  past: [],
  future: [],
  maxHistorySize: 50,

  pushHistory: (nodes: CanvasNode[], edges: CanvasEdge[]) => {
    set((state) => {
      const newEntry: HistoryEntry = {
        nodes: JSON.parse(JSON.stringify(nodes)),
        edges: JSON.parse(JSON.stringify(edges)),
        timestamp: Date.now(),
      }

      const newPast = [...state.past, newEntry].slice(-state.maxHistorySize)

      return {
        past: newPast,
        future: [], // Clear future when new action is performed
      }
    })
  },

  undo: () => {
    const state = get()
    if (state.past.length === 0) return null

    const previous = state.past[state.past.length - 1]
    const newPast = state.past.slice(0, -1)

    set({
      past: newPast,
      future: [previous, ...state.future].slice(0, state.maxHistorySize),
    })

    return {
      nodes: previous.nodes,
      edges: previous.edges,
    }
  },

  redo: () => {
    const state = get()
    if (state.future.length === 0) return null

    const next = state.future[0]
    const newFuture = state.future.slice(1)

    set({
      past: [...state.past, next].slice(-state.maxHistorySize),
      future: newFuture,
    })

    return {
      nodes: next.nodes,
      edges: next.edges,
    }
  },

  canUndo: () => get().past.length > 0,
  canRedo: () => get().future.length > 0,
  clear: () => set({ past: [], future: [] }),
}))
