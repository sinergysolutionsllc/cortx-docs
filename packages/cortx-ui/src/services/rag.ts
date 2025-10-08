/**
 * RAG Service Client
 * Client for interacting with svc-rag (Hierarchical RAG service)
 */

import type {
  RAGQueryRequest,
  RAGQueryResponse,
  RAGRetrieveRequest,
  RAGRetrieveResponse,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentListResponse,
  DocumentFilters
} from '../components/thinktank/types'

export interface RAGServiceConfig {
  /** Base URL for the RAG service (via gateway) */
  baseUrl: string
  /** Optional auth token provider */
  getAuthToken?: () => Promise<string | null>
  /** Optional request interceptor */
  onRequest?: (url: string, init: RequestInit) => void | Promise<void>
}

export class RAGService {
  private config: RAGServiceConfig

  constructor(config: RAGServiceConfig) {
    this.config = config
  }

  private async request<T>(
    endpoint: string,
    init: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(init.headers as Record<string, string>)
    }

    // Add auth token if available
    if (this.config.getAuthToken) {
      const token = await this.config.getAuthToken()
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }

    const requestInit: RequestInit = {
      ...init,
      headers
    }

    // Call request interceptor if provided
    if (this.config.onRequest) {
      await this.config.onRequest(url, requestInit)
    }

    const response = await fetch(url, requestInit)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`RAG Service error: ${response.status} - ${error}`)
    }

    return response.json()
  }

  /**
   * Query the RAG system with hierarchical context
   */
  async query(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    return this.request<RAGQueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Retrieve relevant chunks without LLM generation
   */
  async retrieve(request: RAGRetrieveRequest): Promise<RAGRetrieveResponse> {
    return this.request<RAGRetrieveResponse>('/retrieve', {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Upload a document to the RAG knowledge base
   */
  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', request.file)
    formData.append('title', request.title)
    formData.append('level', request.level)

    if (request.suite_id) formData.append('suite_id', request.suite_id)
    if (request.module_id) formData.append('module_id', request.module_id)
    if (request.description) formData.append('description', request.description)
    if (request.access_level) formData.append('access_level', request.access_level)

    const url = `${this.config.baseUrl}/documents/upload`

    const headers: Record<string, string> = {}

    // Add auth token if available
    if (this.config.getAuthToken) {
      const token = await this.config.getAuthToken()
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }

    const requestInit: RequestInit = {
      method: 'POST',
      headers,
      body: formData
    }

    // Call request interceptor if provided
    if (this.config.onRequest) {
      await this.config.onRequest(url, requestInit)
    }

    const response = await fetch(url, requestInit)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Document upload error: ${response.status} - ${error}`)
    }

    return response.json()
  }

  /**
   * List documents in the knowledge base
   */
  async listDocuments(filters: DocumentFilters = {}): Promise<DocumentListResponse> {
    const params = new URLSearchParams()

    if (filters.level) params.append('level', filters.level)
    if (filters.suite_id) params.append('suite_id', filters.suite_id)
    if (filters.module_id) params.append('module_id', filters.module_id)
    if (filters.limit !== undefined) params.append('limit', String(filters.limit))
    if (filters.offset !== undefined) params.append('offset', String(filters.offset))

    const queryString = params.toString()
    const endpoint = `/documents${queryString ? `?${queryString}` : ''}`

    return this.request<DocumentListResponse>(endpoint, {
      method: 'GET'
    })
  }

  /**
   * Delete a document from the knowledge base
   */
  async deleteDocument(documentId: string): Promise<{ status: string; id: string }> {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE'
    })
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request('/healthz', {
      method: 'GET'
    })
  }

  /**
   * Ready check (includes DB status, document counts, etc.)
   */
  async readyCheck(): Promise<{
    status: string
    database: string
    documents: number
    chunks: number
    embedding_model: string
  }> {
    return this.request('/readyz', {
      method: 'GET'
    })
  }
}

/**
 * Create a RAG service client
 */
export function createRAGService(config: RAGServiceConfig): RAGService {
  return new RAGService(config)
}
