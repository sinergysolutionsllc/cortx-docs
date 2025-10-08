"use client"

import { useState, useRef, useEffect, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { XMarkIcon, ArrowsPointingOutIcon, DocumentCheckIcon } from '@heroicons/react/24/outline'
import { Brain } from 'lucide-react'
import { ThinkTankLogo } from './ThinkTankLogo'
import type { ThinkTankContext, RAGQueryRequest, RAGDocument } from './types'

export interface ThinkTankAssistantProps {
  /** API client for RAG queries */
  ragService: {
    query: (request: RAGQueryRequest) => Promise<any>
    listDocuments: () => Promise<{ documents: RAGDocument[] }>
  }
  /** Current context (suite_id, module_id, etc.) */
  context: ThinkTankContext
  /** Custom example queries to display */
  exampleQueries?: string[]
  /** Callback when assistant is opened */
  onOpen?: () => void
  /** Callback when assistant is closed */
  onClose?: () => void
}

/**
 * ThinkTank AI Assistant - Floating Action Button + Draggable Panel
 *
 * Features:
 * - Pulsing FAB with radiating rings
 * - Draggable glassmorphic mini-panel
 * - Document context awareness
 * - Expand to full-page mode
 * - Suite/Module-specific branding
 */
export function ThinkTankAssistant({
  ragService,
  context,
  exampleQueries,
  onOpen,
  onClose
}: ThinkTankAssistantProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<{
    sql?: string
    summary?: string
    used_documents?: number
    document_sources?: string[]
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadedDocuments, setUploadedDocuments] = useState<RAGDocument[]>([])
  const constraintsRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const closeAssistant = useCallback(() => {
    setOpen(false)
    onClose?.()
    requestAnimationFrame(() => {
      triggerRef.current?.focus()
    })
  }, [onClose])

  const openAssistant = useCallback(() => {
    setOpen(true)
    onOpen?.()
  }, [onOpen])

  const ask = async () => {
    setLoading(true)
    setError(null)
    setAnswer(null)
    try {
      const res = await ragService.query({
        query,
        suite_id: context.suite_id,
        module_id: context.module_id,
        use_documents: uploadedDocuments.length > 0,
        use_cache: true,
        top_k: 5,
        max_tokens: 1000
      })

      setAnswer({
        sql: res.sql,
        summary: res.answer || res.summary,
        used_documents: res.chunks_used || res.used_documents,
        document_sources: res.document_sources
      })
    } catch (e) {
      setError((e as Error)?.message || 'Failed to ask the assistant')
    } finally {
      setLoading(false)
    }
  }

  const loadDocuments = async () => {
    try {
      const docList = await ragService.listDocuments()
      setUploadedDocuments(docList.documents || [])
    } catch (e) {
      console.error('Failed to load documents:', e)
    }
  }

  // Load documents when component opens
  useEffect(() => {
    if (open) {
      loadDocuments()
    }
  }, [open])

  useEffect(() => {
    if (open) {
      inputRef.current?.focus()
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeAssistant()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, closeAssistant])

  // Don't render the assistant if we're on the expanded ThinkTank page
  if (pathname === '/thinktank') {
    return null
  }

  const defaultExamples = [
    "How do I extract data from legacy COBOL systems?",
    "What are NIST compliance requirements for data transformation?",
    "Show me ETL best practices for federal agencies"
  ]

  const examples = exampleQueries || defaultExamples

  return (
    <>
      {/* Fixed position button when closed, draggable when open */}
      {!open && (
        <div className="fixed bottom-6 right-6 z-50">
          {/* Extended radiating pulses - outside the button container */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="absolute h-16 w-16 rounded-full bg-sinergy-teal/20 animate-slow-ping" style={{ animationDelay: '0s' }} />
            <span className="absolute h-20 w-20 rounded-full bg-sinergy-teal/15 animate-slow-ping" style={{ animationDelay: '0.5s' }} />
            <span className="absolute h-24 w-24 rounded-full bg-sinergy-teal/12 animate-slow-ping" style={{ animationDelay: '1s' }} />
            <span className="absolute h-28 w-28 rounded-full bg-sinergy-teal/10 animate-slow-ping" style={{ animationDelay: '1.5s' }} />
            <span className="absolute h-32 w-32 rounded-full bg-sinergy-teal/8 animate-slow-ping" style={{ animationDelay: '2s' }} />
          </div>

          {/* Main button */}
          <motion.button
            type="button"
            ref={triggerRef}
            onClick={openAssistant}
            className="relative z-10 h-14 w-14 rounded-full bg-sinergy-teal text-white shadow-2xl backdrop-blur-md border border-white/20 flex items-center justify-center transition-all duration-300 hover:scale-110 active:scale-95 hover:brightness-95 pointer-events-auto"
            aria-label="Open ThinkTank assistant"
            aria-expanded={open}
            aria-controls="thinktank-panel"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <Brain className="h-6 w-6 text-white animate-pulse" />
          </motion.button>
        </div>
      )}

      {/* Draggable container when open */}
      {open && (
        <div ref={constraintsRef} className="fixed inset-0 pointer-events-none z-50">
          <motion.div
            drag
            dragConstraints={constraintsRef}
            dragElastic={0.1}
            dragMomentum={false}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="absolute bottom-24 right-6 pointer-events-auto"
            whileDrag={{ scale: 1.02, rotate: 1 }}
            role="dialog"
            aria-modal="false"
            aria-labelledby="thinktank-title"
            id="thinktank-panel"
          >
            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="w-[28rem] max-w-[90vw] rounded-2xl border border-white/20 bg-white/10 dark:bg-gray-900/20 shadow-2xl backdrop-blur-xl"
            >
              {/* Glass overlay for extra depth */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/5 to-transparent" />
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-t from-black/5 to-white/5" />

              {/* Draggable header - Gradient background matching page header */}
              <div
                className="relative p-6 border-b border-white/20 flex items-center justify-between cursor-move"
                style={{
                  background: 'linear-gradient(135deg, rgba(0, 194, 203, 0.2) 0%, rgba(0, 0, 0, 0.6) 50%, rgba(45, 89, 114, 0.2) 100%)',
                  backdropFilter: 'blur(20px)'
                }}
                onMouseDown={(e) => {
                  // Allow dragging from header area
                  e.stopPropagation()
                }}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex-1">
                    <div className="flex items-end gap-3">
                      <div className="p-2 rounded-xl bg-sinergy-teal shadow-lg flex items-end">
                        <Brain className="h-8 w-8 text-white" />
                      </div>
                      <div className="flex flex-col gap-0">
                        <ThinkTankLogo size="lg" id="thinktank-title" />
                        <div className="text-xs font-medium text-white/80 whitespace-nowrap">Policy First Guidance, Every Time.</div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="p-2 rounded-xl text-white/60 hover:text-white hover:bg-white/20 transition-all duration-200 shadow-sm"
                      onClick={() => router.push('/thinktank')}
                      title="Expand to full page"
                      aria-label="Open ThinkTank in full page"
                    >
                      <ArrowsPointingOutIcon className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      className="p-2 rounded-xl text-white hover:text-gray-200 hover:bg-white/20 transition-all duration-200 shadow-sm"
                      onClick={closeAssistant}
                      aria-label="Close ThinkTank assistant"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Content area with enhanced styling and scroll */}
              <div className="relative p-6 space-y-4 max-h-[70vh] overflow-y-auto">
                {/* Document Context Status */}
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

                {/* Example queries for ETL and policy guidance */}
                {!answer && !error && !loading && (
                  <div className="space-y-3">
                    <div className="text-xs font-medium text-white/80 mb-2">Try asking about:</div>
                    <div className="grid gap-2">
                      {examples.map((example, index) => (
                        <button
                          key={index}
                          onClick={() => setQuery(example)}
                          className="text-left text-xs p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white/90 hover:text-white transition-all border border-white/20 hover:border-white/30"
                        >
                          💡 {example}
                        </button>
                      ))}
                      {uploadedDocuments.length > 0 && (
                        <button
                          onClick={() => setQuery("Analyze the uploaded documents and tell me about key topics")}
                          className="text-left text-xs p-2 rounded-lg bg-sinergy-teal/20 hover:bg-sinergy-teal/30 text-white/90 hover:text-white transition-all border border-sinergy-teal/30 hover:border-sinergy-teal/40"
                        >
                          📄 "Analyze the uploaded documents and tell me about key topics"
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Modern input with glassmorphism */}
                <div className="relative">
                  <input
                    ref={inputRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about ETL processes, policy compliance, or data transformations..."
                    aria-label="Ask ThinkTank"
                    className="w-full rounded-2xl border-2 border-white/30 px-5 py-4 bg-white/20 dark:bg-gray-800/30 backdrop-blur-sm placeholder:text-gray-600 dark:placeholder:text-gray-400 placeholder:font-medium focus:outline-none focus:ring-2 focus:ring-sinergy-teal focus:border-sinergy-teal focus:bg-white/30 dark:focus:bg-gray-800/40 transition-all duration-300 text-gray-900 dark:text-white font-medium shadow-lg"
                    onKeyDown={(e) => { if (e.key === 'Enter') ask() }}
                  />
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />
                </div>

                {/* Modern buttons with reactive styling */}
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={ask}
                    disabled={loading || !query.trim()}
                    className="relative overflow-hidden flex-1 px-6 py-3 rounded-xl bg-gradient-to-r from-sinergy-teal to-sinergy-teal-600 text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl hover:shadow-sinergy-teal/30 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] group shadow-lg"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/0 group-hover:from-white/20 transition-all duration-300" />
                    <span className="relative z-10 flex items-center justify-center gap-2 drop-shadow-sm">
                      {loading && (
                        <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                      )}
                      {loading ? 'Analyzing…' : 'Ask ThinkTank'}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => { setQuery(''); setAnswer(null); setError(null) }}
                    className="relative overflow-hidden px-6 py-3 rounded-xl border-2 border-white/30 bg-white/10 dark:bg-gray-800/30 backdrop-blur-sm text-gray-800 dark:text-gray-200 font-bold hover:bg-white/20 dark:hover:bg-gray-700/40 hover:border-white/40 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] group shadow-lg"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent group-hover:from-white/15 transition-all duration-300" />
                    <span className="relative z-10 drop-shadow-sm">Clear</span>
                  </button>
                </div>

                {/* Enhanced error display */}
                {error && (
                  <div className="relative p-4 rounded-xl border-2 border-red-500/40 bg-red-500/20 backdrop-blur-sm text-red-800 dark:text-red-200 text-sm font-medium animate-in fade-in duration-200 shadow-lg">
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-red-500/10 to-transparent" />
                    <div className="relative z-10 drop-shadow-sm">{error}</div>
                  </div>
                )}

                {/* Enhanced answer display */}
                {answer && (
                  <div className="space-y-4 text-sm animate-in fade-in duration-300">
                    {answer.summary && (
                      <div className="relative p-4 rounded-xl border-2 border-sinergy-teal/40 bg-sinergy-teal/20 backdrop-blur-sm shadow-lg">
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-sinergy-teal/10 to-federal-navy/10" />
                        <div className="relative z-10">
                          <div className="flex items-center gap-2 font-bold text-white mb-3">
                            <div className="w-3 h-3 rounded-full bg-white shadow-lg animate-pulse" />
                            Summary
                          </div>
                          <div className="text-gray-100 dark:text-gray-100 whitespace-pre-wrap leading-relaxed font-medium">
                            {answer.summary}
                          </div>
                        </div>
                      </div>
                    )}
                    {answer.sql && (
                      <div className="relative p-4 rounded-xl border-2 border-white/30 bg-white/10 dark:bg-gray-800/30 backdrop-blur-sm shadow-lg">
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/10 to-transparent" />
                        <div className="relative z-10">
                          <div className="flex items-center gap-2 font-bold text-white mb-3">
                            <div className="w-3 h-3 rounded-full bg-green-500 shadow-lg animate-pulse" />
                            SQL Query
                          </div>
                          <div className="relative">
                            <pre className="bg-gray-900/50 dark:bg-gray-900/70 border-2 border-white/20 p-4 rounded-xl overflow-auto text-sm backdrop-blur-sm shadow-inner">
                              <code className="text-gray-100 dark:text-gray-100 font-mono font-medium">
                                {answer.sql}
                              </code>
                            </pre>
                            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none" />
                          </div>
                        </div>
                      </div>
                    )}
                    {answer.document_sources && answer.document_sources.length > 0 && (
                      <div className="relative p-4 rounded-xl border-2 border-blue-500/40 bg-blue-500/20 backdrop-blur-sm shadow-lg">
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-500/10 to-transparent" />
                        <div className="relative z-10">
                          <div className="flex items-center gap-2 font-bold text-white mb-3">
                            <DocumentCheckIcon className="h-4 w-4 text-blue-400" />
                            Document Sources ({answer.used_documents})
                          </div>
                          <div className="space-y-1">
                            {answer.document_sources.map((source, index) => (
                              <div key={index} className="text-xs text-blue-100 bg-blue-500/20 px-2 py-1 rounded">
                                📄 {source}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Security footer */}
                <div className="pt-2 text-center">
                  <span className="text-[11px] text-white/60">
                    Secured by <span className="text-white">CORT</span><span className="text-sinergy-teal">X</span> • Audit logged
                  </span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      )}
    </>
  )
}
