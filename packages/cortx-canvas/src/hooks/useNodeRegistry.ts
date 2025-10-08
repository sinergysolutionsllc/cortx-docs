import { create } from 'zustand'
import { NodeTypeDefinition, NodeRegistry } from '../types'

interface NodeRegistryStore {
  definitions: Map<string, NodeTypeDefinition>
  register: (definition: NodeTypeDefinition) => void
  unregister: (type: string) => void
  get: (type: string) => NodeTypeDefinition | undefined
  getAll: () => NodeTypeDefinition[]
  getByCategory: (category: string) => NodeTypeDefinition[]
  search: (query: string) => NodeTypeDefinition[]
}

export const useNodeRegistry = create<NodeRegistryStore>((set, get) => ({
  definitions: new Map(),

  register: (definition: NodeTypeDefinition) => {
    set((state) => {
      const newDefinitions = new Map(state.definitions)
      newDefinitions.set(definition.type, definition)
      return { definitions: newDefinitions }
    })
  },

  unregister: (type: string) => {
    set((state) => {
      const newDefinitions = new Map(state.definitions)
      newDefinitions.delete(type)
      return { definitions: newDefinitions }
    })
  },

  get: (type: string) => {
    return get().definitions.get(type)
  },

  getAll: () => {
    return Array.from(get().definitions.values())
  },

  getByCategory: (category: string) => {
    return Array.from(get().definitions.values()).filter(
      (def) => def.category === category
    )
  },

  search: (query: string) => {
    const lowerQuery = query.toLowerCase()
    return Array.from(get().definitions.values()).filter(
      (def) =>
        def.label.toLowerCase().includes(lowerQuery) ||
        def.description.toLowerCase().includes(lowerQuery) ||
        def.type.toLowerCase().includes(lowerQuery) ||
        def.tags?.some((tag) => tag.toLowerCase().includes(lowerQuery))
    )
  },
}))

// Export a registry object that implements NodeRegistry interface
export const nodeRegistry: NodeRegistry = {
  register: (definition: NodeTypeDefinition) => useNodeRegistry.getState().register(definition),
  unregister: (type: string) => useNodeRegistry.getState().unregister(type),
  get: (type: string) => useNodeRegistry.getState().get(type),
  getAll: () => useNodeRegistry.getState().getAll(),
  getByCategory: (category: string) => useNodeRegistry.getState().getByCategory(category),
  search: (query: string) => useNodeRegistry.getState().search(query),
}
