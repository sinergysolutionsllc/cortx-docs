/**
 * ThinkTank Component Types
 * Shared type definitions for the ThinkTank AI assistant
 */

export interface ThinkTankMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sql?: string
  used_documents?: number
  document_sources?: string[]
  timestamp: Date
}

export interface ThinkTankContext {
  suite_id?: string | null
  module_id?: string | null
  entity_id?: string | null
  route?: string
  user_id?: string
  user_role?: string
}

export interface RAGQueryRequest {
  query: string
  suite_id?: string | null
  module_id?: string | null
  use_cache?: boolean
  use_hybrid?: boolean
  use_documents?: boolean
  top_k?: number
  max_tokens?: number
}

export interface RAGQueryResponse {
  query: string
  answer: string
  chunks_used: number
  document_sources: string[]
  model: string
  tokens_used: number
  cache_hit: boolean
  correlation_id: string
}

export interface RAGRetrieveRequest {
  query: string
  suite_id?: string | null
  module_id?: string | null
  top_k?: number
  use_hybrid?: boolean
}

export interface RAGRetrievedChunk {
  chunk_id: string
  document_id: string
  document_title: string
  document_level: string
  heading?: string
  content: string
  similarity: number
  context_boost: number
  final_score: number
}

export interface RAGRetrieveResponse {
  query: string
  chunks: RAGRetrievedChunk[]
  retrieval_time_ms: number
}

export interface DocumentUploadRequest {
  file: File
  title: string
  level: 'platform' | 'suite' | 'module' | 'entity'
  suite_id?: string | null
  module_id?: string | null
  description?: string
  access_level?: 'public' | 'internal' | 'confidential' | 'restricted'
}

export interface DocumentUploadResponse {
  id: string
  title: string
  level: string
  chunks_count: number
  status: string
}

export interface RAGDocument {
  id: string
  title: string
  level: string
  suite_id?: string | null
  module_id?: string | null
  source_type: string
  created_at: string
  chunk_count: number
}

export interface DocumentListResponse {
  documents: RAGDocument[]
  total: number
  limit: number
  offset: number
}

export interface DocumentFilters {
  level?: string
  suite_id?: string
  module_id?: string
  limit?: number
  offset?: number
}
