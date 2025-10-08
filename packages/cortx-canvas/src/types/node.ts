import { ComponentType } from 'react'

export interface NodeTypeDefinition {
  type: string
  label: string
  description: string
  category: string
  icon: ComponentType<any>
  color: string
  shape?: 'rectangle' | 'circle' | 'diamond' | 'hexagon' | 'rounded'
  ports: {
    input: boolean
    output: boolean
    multipleOutputs?: boolean
    outputLabels?: string[]
  }
  defaultData?: Record<string, any>
  properties?: NodeProperty[]
  validations?: NodeValidation[]
  tags?: string[]
}

export interface NodeProperty {
  key: string
  label: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'multiselect' | 'textarea' | 'json' | 'code'
  required?: boolean
  default?: any
  description?: string
  placeholder?: string
  options?: Array<{ value: string; label: string }>
  min?: number
  max?: number
  pattern?: string
  validation?: (value: any) => string | null
}

export interface NodeValidation {
  field: string
  rule: 'required' | 'min' | 'max' | 'pattern' | 'custom'
  value?: any
  message: string
  validator?: (data: any) => boolean
}

export interface NodeCategory {
  id: string
  label: string
  description?: string
  icon?: ComponentType<any>
  color?: string
  order?: number
}

export interface NodeRegistry {
  register(definition: NodeTypeDefinition): void
  unregister(type: string): void
  get(type: string): NodeTypeDefinition | undefined
  getAll(): NodeTypeDefinition[]
  getByCategory(category: string): NodeTypeDefinition[]
  search(query: string): NodeTypeDefinition[]
}

export interface NodePaletteConfig {
  categories?: NodeCategory[]
  searchable?: boolean
  collapsible?: boolean
  defaultExpanded?: boolean
  showIcons?: boolean
  groupByCategory?: boolean
}
