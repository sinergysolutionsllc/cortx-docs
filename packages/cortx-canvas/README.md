# @sinergysolutions/cortx-canvas

Visual workflow canvas component with AI-assisted design for CORTX suites.

## Features

- 🎨 **Beautiful UI** - Modern, polished design with smooth animations
- 🔌 **Plugin Architecture** - Extensible node type system
- 📊 **Auto-Layout** - Dagre and ELK layout algorithms
- 💾 **Export** - PNG, SVG, JPEG, and JSON export
- ⏮️ **Undo/Redo** - Full history with timeline
- 🎯 **Drag & Drop** - Intuitive node palette
- 🔍 **Search** - Fast node search and filtering
- ♿ **Accessible** - WCAG AA compliant
- 🎭 **TypeScript** - Fully typed
- 🎨 **Themeable** - Tailwind CSS integration

## Installation

```bash
npm install @sinergysolutions/cortx-canvas
```

### Peer Dependencies

```bash
npm install react react-dom reactflow
```

## Quick Start

```tsx
import { Canvas, NodePalette, Toolbar, nodeRegistry } from '@sinergysolutions/cortx-canvas'
import { Play, Square } from 'lucide-react'

// Register node types
nodeRegistry.register({
  type: 'start',
  label: 'Start',
  description: 'Start node',
  category: 'Flow Control',
  icon: Play,
  color: 'bg-green-500',
  ports: { input: false, output: true },
  tags: ['flow'],
})

nodeRegistry.register({
  type: 'end',
  label: 'End',
  description: 'End node',
  category: 'Flow Control',
  icon: Square,
  color: 'bg-red-500',
  ports: { input: true, output: false },
  tags: ['flow'],
})

function MyWorkflowDesigner() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])

  return (
    <div className="flex h-screen">
      <NodePalette />
      <Canvas
        nodes={nodes}
        edges={edges}
        callbacks={{
          onNodesChange: setNodes,
          onEdgesChange: setEdges,
        }}
      >
        <Toolbar onSave={() => console.log('Save')} />
      </Canvas>
    </div>
  )
}
```

## API

### Canvas

Main canvas component.

```tsx
<Canvas
  nodes={nodes}
  edges={edges}
  config={{
    snapToGrid: true,
    gridSize: 15,
    fitViewOnInit: true,
  }}
  callbacks={{
    onNodesChange: handleNodesChange,
    onEdgesChange: handleEdgesChange,
    onNodeClick: handleNodeClick,
  }}
  showMinimap
  showControls
  showBackground
/>
```

### NodePalette

Draggable node palette with search and categories.

```tsx
<NodePalette
  config={{
    searchable: true,
    collapsible: true,
    groupByCategory: true,
  }}
  onNodeAdd={handleNodeAdd}
/>
```

### Toolbar

Toolbar with undo/redo, zoom, export, and auto-layout.

```tsx
<Toolbar
  onSave={handleSave}
  onExport={handleExport}
  onAutoLayout={handleAutoLayout}
  onUndo={handleUndo}
  onRedo={handleRedo}
/>
```

### Node Registry

Register custom node types.

```tsx
import { nodeRegistry } from '@sinergysolutions/cortx-canvas'
import { Database } from 'lucide-react'

nodeRegistry.register({
  type: 'database',
  label: 'Database',
  description: 'Database operation',
  category: 'Data',
  icon: Database,
  color: 'bg-blue-500',
  ports: {
    input: true,
    output: true,
    multipleOutputs: true,
    outputLabels: ['Success', 'Error'],
  },
  properties: [
    {
      key: 'connectionString',
      label: 'Connection String',
      type: 'text',
      required: true,
    },
    {
      key: 'query',
      label: 'SQL Query',
      type: 'code',
      required: true,
    },
  ],
  tags: ['data', 'database'],
})
```

### Auto-Layout

```tsx
import { autoLayout } from '@sinergysolutions/cortx-canvas'

const layoutedNodes = await autoLayout(nodes, edges, {
  algorithm: 'dagre', // or 'elk-layered', 'elk-force'
  direction: 'TB', // or 'LR', 'BT', 'RL'
  nodeSpacing: 50,
  rankSpacing: 100,
})

setNodes(layoutedNodes)
```

### Export

```tsx
import { exportCanvas } from '@sinergysolutions/cortx-canvas'

// Get canvas element
const canvasElement = document.querySelector('.react-flow')

// Export to PNG
await exportCanvas('png', canvasElement, nodes, edges, {
  quality: 1,
  backgroundColor: '#ffffff',
  padding: 20,
})

// Export to JSON
await exportCanvas('json', canvasElement, nodes, edges)
```

### History

```tsx
import { useCanvasHistory } from '@sinergysolutions/cortx-canvas'

const pushHistory = useCanvasHistory((state) => state.pushHistory)
const undo = useCanvasHistory((state) => state.undo)
const redo = useCanvasHistory((state) => state.redo)
const canUndo = useCanvasHistory((state) => state.canUndo())
const canRedo = useCanvasHistory((state) => state.canRedo())

// Push to history after changes
pushHistory(nodes, edges)

// Undo
const previous = undo()
if (previous) {
  setNodes(previous.nodes)
  setEdges(previous.edges)
}

// Redo
const next = redo()
if (next) {
  setNodes(next.nodes)
  setEdges(next.edges)
}
```

## Styling

Import the CSS in your app:

```tsx
import '@sinergysolutions/cortx-canvas/dist/index.css'
```

Or use Tailwind CSS (recommended):

```js
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@sinergysolutions/cortx-canvas/dist/**/*.{js,mjs}',
  ],
  // ...
}
```

## Examples

See the `/examples` directory for complete examples:

- Basic workflow designer
- BPMN designer
- Data pipeline designer
- AI-assisted workflow

## License

PROPRIETARY - Sinergy Solutions LLC
