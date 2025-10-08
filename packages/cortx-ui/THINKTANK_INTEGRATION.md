# ThinkTank Integration Guide

ThinkTank is a hierarchical RAG-powered AI assistant for the CORTX Platform. This guide shows you how to integrate ThinkTank into your Suite or Module application.

## Features

- ✅ **Floating Action Button (FAB)** with pulsing animations
- ✅ **Draggable mini-panel** with glassmorphic design
- ✅ **Full-page chat interface**
- ✅ **Hierarchical context awareness** (Platform → Suite → Module → Entity)
- ✅ **Document-augmented responses** with citations
- ✅ **Semantic caching** for faster responses
- ✅ **Suite/Module-specific branding**

## Installation

ThinkTank is already included in `@sinergysolutions/cortx-ui`. Make sure you have the required peer dependencies:

```bash
npm install @heroicons/react framer-motion lucide-react next
```

## Quick Start

### 1. Create RAG Service Instance

```typescript
// lib/rag.ts
import { createRAGService } from '@sinergysolutions/cortx-ui'

export const ragService = createRAGService({
  baseUrl: process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8080',
  getAuthToken: async () => {
    // Return your auth token here
    const token = localStorage.getItem('auth_token')
    return token
  }
})
```

### 2. Add ThinkTank Assistant to Your Layout

```tsx
// components/layout/DashboardLayout.tsx
'use client'

import { ThinkTankAssistant, useThinkTankContext } from '@sinergysolutions/cortx-ui'
import { ragService } from '@/lib/rag'

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const context = useThinkTankContext()

  return (
    <div className="min-h-screen bg-gradient-to-br from-federal-navy via-clarity-blue-900 to-slate-gray-900">
      {children}

      {/* ThinkTank FAB + Panel */}
      <ThinkTankAssistant
        ragService={ragService}
        context={context}
        exampleQueries={[
          "How do I extract data from legacy COBOL systems?",
          "What are NIST compliance requirements?",
          "Show me ETL best practices for federal agencies"
        ]}
      />
    </div>
  )
}
```

### 3. Create Full-Page ThinkTank Route

```tsx
// app/thinktank/page.tsx
'use client'

import { ThinkTankPage, useThinkTankContext } from '@sinergysolutions/cortx-ui'
import { ragService } from '@/lib/rag'
import DashboardLayout from '@/components/layout/DashboardLayout'

export default function ThinkTankFullPage() {
  const context = useThinkTankContext()

  return (
    <ThinkTankPage
      ragService={ragService}
      context={context}
      LayoutWrapper={DashboardLayout}
      exampleQueries={[
        "How do I configure ETL pipelines?",
        "What compliance frameworks apply to my data?",
        "Explain the DataFlow module architecture"
      ]}
    />
  )
}
```

## Advanced Usage

### Custom RAG Service Configuration

```typescript
import { createRAGService } from '@sinergysolutions/cortx-ui'

const ragService = createRAGService({
  baseUrl: 'https://api.cortx.example.com',
  getAuthToken: async () => {
    // Custom auth logic
    return await getAccessToken()
  },
  onRequest: async (url, init) => {
    // Add custom headers or logging
    console.log(`RAG Request: ${url}`)
  }
})
```

### Context Detection

ThinkTank automatically detects suite and module from the URL:

```
/fedsuite/dataflow/... → { suite_id: 'fedsuite', module_id: 'dataflow' }
/fedsuite/...          → { suite_id: 'fedsuite', module_id: null }
/thinktank             → { suite_id: null, module_id: null }
```

You can also provide custom context:

```typescript
const context = {
  suite_id: 'fedsuite',
  module_id: 'dataflow',
  entity_id: tenantId,
  user_id: userId,
  user_role: userRole
}
```

### Document Upload

```typescript
import { ragService } from '@/lib/rag'

async function uploadDocument(file: File) {
  const result = await ragService.uploadDocument({
    file,
    title: "My Policy Document",
    level: "module",           // platform | suite | module | entity
    suite_id: "fedsuite",
    module_id: "dataflow",
    description: "ETL best practices",
    access_level: "internal"
  })

  console.log(`Uploaded document: ${result.id} with ${result.chunks_count} chunks`)
}
```

### List Documents

```typescript
const documents = await ragService.listDocuments({
  level: 'module',
  suite_id: 'fedsuite',
  module_id: 'dataflow',
  limit: 50,
  offset: 0
})

console.log(`Found ${documents.total} documents`)
documents.documents.forEach(doc => {
  console.log(`- ${doc.title} (${doc.chunk_count} chunks)`)
})
```

### Direct RAG Query

```typescript
const response = await ragService.query({
  query: "How do I extract COBOL data?",
  suite_id: "fedsuite",
  module_id: "dataflow",
  use_cache: true,
  use_hybrid: false,
  top_k: 5,
  max_tokens: 1000
})

console.log(response.answer)
console.log(`Used ${response.chunks_used} chunks from:`, response.document_sources)
```

### Retrieve Only (No LLM)

```typescript
const chunks = await ragService.retrieve({
  query: "COBOL data extraction",
  suite_id: "fedsuite",
  module_id: "dataflow",
  top_k: 5,
  use_hybrid: true
})

chunks.chunks.forEach(chunk => {
  console.log(`${chunk.document_title}: ${chunk.content.substring(0, 100)}...`)
  console.log(`  Similarity: ${chunk.similarity}, Boost: ${chunk.context_boost}`)
})
```

## Styling

ThinkTank uses Tailwind CSS with CORTX design tokens. Make sure your `tailwind.config.ts` includes the CORTX color palette:

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  theme: {
    extend: {
      colors: {
        'sinergy-teal': {
          DEFAULT: '#00C2CB',
          50: '#B3F0F3',
          100: '#9EEDF0',
          // ... other shades
        },
        'federal-navy': {
          DEFAULT: '#2D5972',
          // ... other shades
        },
        // ... other CORTX colors
      }
    }
  }
}
```

## Customization

### Custom Example Queries

```tsx
<ThinkTankAssistant
  ragService={ragService}
  context={context}
  exampleQueries={[
    "Explain the reconciliation process",
    "What GTAS rules apply here?",
    "Show me treasury account mappings"
  ]}
/>
```

### Lifecycle Hooks

```tsx
<ThinkTankAssistant
  ragService={ragService}
  context={context}
  onOpen={() => console.log('ThinkTank opened')}
  onClose={() => console.log('ThinkTank closed')}
/>
```

## API Reference

### `ThinkTankAssistant`

Floating button + draggable panel component.

**Props:**

- `ragService: RAGService` - RAG service client instance
- `context: ThinkTankContext` - Current context (suite, module, etc.)
- `exampleQueries?: string[]` - Custom example queries to display
- `onOpen?: () => void` - Called when assistant is opened
- `onClose?: () => void` - Called when assistant is closed

### `ThinkTankPage`

Full-page chat interface.

**Props:**

- `ragService: RAGService` - RAG service client instance
- `context: ThinkTankContext` - Current context (suite, module, etc.)
- `exampleQueries?: string[]` - Custom example queries to display
- `LayoutWrapper?: React.ComponentType` - Optional layout wrapper component

### `useThinkTankContext`

Hook to automatically detect suite/module from URL.

**Returns:** `ThinkTankContext`

```typescript
const context = useThinkTankContext(userId, userRole)
// → { suite_id: 'fedsuite', module_id: 'dataflow', route: '/fedsuite/dataflow/...', user_id, user_role }
```

### `createRAGService`

Factory function to create RAG service client.

**Parameters:**

- `config: RAGServiceConfig`
  - `baseUrl: string` - Base URL for RAG service (via gateway)
  - `getAuthToken?: () => Promise<string | null>` - Auth token provider
  - `onRequest?: (url, init) => void` - Request interceptor

**Returns:** `RAGService`

## Troubleshooting

### FAB not appearing

1. Check that you're not on `/thinktank` page (FAB is hidden there)
2. Verify ThinkTankAssistant is rendered in your layout
3. Check z-index conflicts (FAB uses `z-50`)

### No documents found

1. Verify svc-rag is running and accessible
2. Check document upload success
3. Verify access_level permissions
4. Check tenant_id isolation

### API errors

1. Verify gateway URL is correct
2. Check auth token is valid
3. Review svc-rag logs for errors
4. Test with `/rag/healthz` endpoint

## Examples

See full working examples in:

- `fedsuite/frontend/app` - FedSuite integration
- `cortx-dataflow/ui/app/thinktank` - Original implementation

## Support

For issues or questions:

- GitHub Issues: <https://github.com/sinergysolutionsllc/cortx-ui/issues>
- Slack: #thinktank-support
