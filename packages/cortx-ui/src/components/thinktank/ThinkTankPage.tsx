"use client"

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { DocumentCheckIcon, PaperAirplaneIcon, ArrowsPointingInIcon } from '@heroicons/react/24/outline'
import { Brain } from 'lucide-react'
import { ThinkTankLogo } from './ThinkTankLogo'
import type { ThinkTankMessage, ThinkTankContext, RAGQueryRequest, RAGDocument } from './types'

export interface ThinkTankPageProps {
  /** API client for RAG queries */
  ragService: {
    query: (request: RAGQueryRequest) => Promise<any>
    listDocuments: () => Promise<{ documents: RAGDocument[] }>
  }
  /** Current context (suite_id, module_id, etc.) */
  context: ThinkTankContext
  /** Custom example queries to display */
  exampleQueries?: string[]
  /** Optional layout wrapper component */
  LayoutWrapper?: React.ComponentType<{ children: React.ReactNode }>
}

/**
 * ThinkTank Full-Page Chat Interface
 *
 * Features:
 * - Full conversation history
 * - Message bubbles (user vs assistant)
 * - SQL code blocks with syntax highlighting
 * - Document source citations
 * - Auto-scroll to latest message
 * - Collapse back to FAB
 */
export function ThinkTankPage({
  ragService,
  context,
  exampleQueries,
  LayoutWrapper
}: ThinkTankPageProps) {
  const router = useRouter()
  const [messages, setMessages] = useState<ThinkTankMessage[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadedDocuments, setUploadedDocuments] = useState<RAGDocument[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const docList = await ragService.listDocuments()
      setUploadedDocuments(docList.documents || [])
    } catch (e) {
      console.error('Failed to load documents:', e)
    }
  }

  const ask = async () => {
    if (!query.trim()) return

    const userMessage: ThinkTankMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setQuery('')
    setLoading(true)
    setError(null)

    try {
      const res = await ragService.query({
        query: userMessage.content,
        suite_id: context.suite_id,
        module_id: context.module_id,
        use_documents: uploadedDocuments.length > 0,
        use_cache: true,
        top_k: 5,
        max_tokens: 1000
      })

      const assistantMessage: ThinkTankMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.answer || res.summary || 'No response',
        sql: res.sql,
        used_documents: res.chunks_used || res.used_documents,
        document_sources: res.document_sources,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (e) {
      setError((e as Error)?.message || 'Failed to ask the assistant')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      ask()
    }
  }

  const defaultExamples = [
    "How do I extract data from legacy COBOL systems?",
    "What are NIST compliance requirements for data transformation?",
    "Show me ETL best practices for federal agencies",
    "Analyze the uploaded schema and tell me about the table structures"
  ]

  const examples = exampleQueries || defaultExamples

  const content = (
    <>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-end gap-4 mb-2">
          <div className="p-3 rounded-2xl bg-gradient-to-br from-sinergy-teal to-sinergy-teal-600 shadow-lg">
            <Brain className="h-10 w-10 text-white" />
          </div>
          <div className="flex flex-col gap-0 flex-1">
            <ThinkTankLogo size="lg" />
            <div className="text-sm font-medium text-white/70">Policy First Guidance, Every Time.</div>
          </div>
          <button
            onClick={() => router.back()}
            className="p-3 rounded-2xl text-white/60 hover:text-white hover:bg-white/20 transition-all duration-200 border border-white/20 hover:border-sinergy-teal/50"
            title="Collapse to floating assistant"
          >
            <ArrowsPointingInIcon className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="grid grid-cols-1 gap-6">
        <div className="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-xl shadow-2xl overflow-hidden">
          <div className="p-6">
            {/* Document Context Banner */}
            {uploadedDocuments.length > 0 && (
              <div className="mb-4 p-3 rounded-lg bg-green-500/20 border border-green-500/30">
                <div className="flex items-center gap-2">
                  <DocumentCheckIcon className="h-4 w-4 text-green-400" />
                  <span className="text-sm text-green-300 font-medium">
                    Document context active ({uploadedDocuments.length} documents available)
                  </span>
                </div>
                <div className="text-xs text-green-200/80 mt-1">
                  ThinkTank will automatically search uploaded documents to enhance responses.
                </div>
              </div>
            )}

            {/* Messages Area */}
            <div className="min-h-[500px] max-h-[600px] overflow-y-auto mb-4 space-y-4 p-4 bg-black/20 rounded-xl">
              {messages.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center h-full space-y-6 py-12">
                  <div className="text-center">
                    <h3 className="text-xl font-heading font-semibold text-white mb-2">
                      Welcome to <span className="text-sinergy-teal">Think</span><span className="text-white">Tank<sup className="text-xs align-super ml-0.5">™</sup></span>
                    </h3>
                    <p className="text-white/60 mb-6">
                      Ask anything about processes, policy compliance, or platform capabilities
                    </p>
                  </div>

                  {/* Example Queries */}
                  <div className="w-full max-w-2xl space-y-2">
                    <div className="text-xs font-medium text-white/60 mb-3">Try asking about:</div>
                    <div className="grid gap-2">
                      {examples.map((example, index) => (
                        <button
                          key={index}
                          onClick={() => setQuery(example)}
                          className="text-left text-sm p-3 rounded-lg bg-white/10 hover:bg-white/20 text-white/90 hover:text-white transition-all border border-white/20 hover:border-sinergy-teal/50"
                        >
                          💡 {example}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl p-4 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-sinergy-teal to-sinergy-teal-600 text-white'
                        : 'bg-white/10 border border-white/20 text-white'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>

                    {message.sql && (
                      <div className="mt-3 p-3 bg-black/30 rounded-lg border border-white/10">
                        <div className="text-xs font-semibold text-green-400 mb-2">SQL Query:</div>
                        <pre className="text-xs text-gray-300 overflow-x-auto">
                          <code>{message.sql}</code>
                        </pre>
                      </div>
                    )}

                    {message.document_sources && message.document_sources.length > 0 && (
                      <div className="mt-3 p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
                        <div className="flex items-center gap-2 text-xs font-semibold text-blue-400 mb-2">
                          <DocumentCheckIcon className="h-3 w-3" />
                          Document Sources ({message.used_documents})
                        </div>
                        <div className="space-y-1">
                          {message.document_sources.map((source, index) => (
                            <div key={index} className="text-xs text-blue-200 bg-blue-500/10 px-2 py-1 rounded">
                              📄 {source}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="text-xs text-white/40 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </motion.div>
              ))}

              {loading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="max-w-[80%] rounded-xl p-4 bg-white/10 border border-white/20">
                    <div className="flex items-center gap-2 text-white">
                      <div className="w-2 h-2 bg-sinergy-teal rounded-full animate-pulse" />
                      <div className="w-2 h-2 bg-sinergy-teal rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                      <div className="w-2 h-2 bg-sinergy-teal rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                      <span className="ml-2 text-sm">ThinkTank is analyzing...</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {error && (
                <div className="p-4 rounded-xl border-2 border-red-500/40 bg-red-500/20 text-red-200 text-sm">
                  {error}
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="relative">
              <div className="flex gap-3">
                <textarea
                  ref={textareaRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about processes, policy compliance, or platform capabilities..."
                  className="flex-1 min-h-[60px] max-h-[200px] rounded-xl border-2 border-white/30 px-4 py-3 bg-white/10 backdrop-blur-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-sinergy-teal focus:border-sinergy-teal transition-all duration-300 text-white resize-none"
                  rows={2}
                />
                <button
                  onClick={ask}
                  disabled={loading || !query.trim()}
                  className="px-6 rounded-xl bg-gradient-to-r from-sinergy-teal to-sinergy-teal-600 text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl hover:shadow-sinergy-teal/30 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  ) : (
                    <PaperAirplaneIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              <div className="mt-2 flex items-center justify-between text-xs">
                <span className="text-white/40">Press Enter to send, Shift + Enter for new line</span>
                <span className="text-white/40">
                  Secured by <span className="text-white">CORT</span><span className="text-sinergy-teal">X</span> • Audit logged
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )

  if (LayoutWrapper) {
    return <LayoutWrapper>{content}</LayoutWrapper>
  }

  return content
}
