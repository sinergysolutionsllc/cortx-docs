/**
 * ThinkTank AI Assistant Components
 * Hierarchical RAG-powered AI guidance system
 */

export { ThinkTankLogo } from './ThinkTankLogo'
export type { ThinkTankLogoProps } from './ThinkTankLogo'

export { ThinkTankAssistant } from './ThinkTankAssistant'
export type { ThinkTankAssistantProps } from './ThinkTankAssistant'

export { ThinkTankPage } from './ThinkTankPage'
export type { ThinkTankPageProps } from './ThinkTankPage'

export type {
  ThinkTankMessage,
  ThinkTankContext,
  RAGQueryRequest,
  RAGQueryResponse,
  RAGRetrieveRequest,
  RAGRetrieveResponse,
  RAGRetrievedChunk,
  DocumentUploadRequest,
  DocumentUploadResponse,
  RAGDocument,
  DocumentListResponse,
  DocumentFilters
} from './types'
