import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Bot,
  ChevronDown,
  Copy,
  Check,
  ThumbsDown,
  ThumbsUp,
  RefreshCw,
  AlertTriangle,
  BookOpen,
  Brain,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { cn, formatDateTime } from '@/utils'
import { TypingIndicator } from '@/components/common/TypingIndicator'

interface AIResponseCardProps {
  content: string
  role: 'user' | 'assistant'
  timestamp?: string
  domain?: string
  confidence?: number | null
  reason?: string | null
  sources?: string[]
  warning?: string
  explainability?: Record<string, unknown>
  isStreaming?: boolean
  onRegenerate?: () => void
}

export function AIResponseCard({
  content,
  role,
  timestamp,
  domain,
  confidence,
  reason,
  sources,
  warning,
  explainability,
  isStreaming,
  onRegenerate,
}: AIResponseCardProps) {
  const [copied, setCopied] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const isUser = role === 'user'

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex gap-3', isUser && 'flex-row-reverse')}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary'
        )}
      >
        {isUser ? (
          <span className="text-xs font-bold">You</span>
        ) : (
          <Bot className="h-4 w-4 text-primary" />
        )}
      </div>

      <div className={cn('flex flex-col gap-2 max-w-[85%]', isUser && 'items-end')}>
        <Card className={cn(isUser ? 'bg-primary text-primary-foreground border-primary' : 'glass')}>
          <CardContent className="p-4">
            {isStreaming && !content ? (
              <TypingIndicator />
            ) : isUser ? (
              <p className="text-sm">{content}</p>
            ) : (
              <div className="prose-chat">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              </div>
            )}
          </CardContent>
        </Card>

        {!isUser && !isStreaming && (
          <div className="flex flex-wrap items-center gap-2">
            {domain && (
              <Badge variant={domain as 'career' | 'health' | 'finance'} className="text-[10px] capitalize">
                {domain}
              </Badge>
            )}
            {confidence != null && (
              <Badge variant="secondary" className="text-[10px]">
                {Math.round(confidence * 100)}% confidence
              </Badge>
            )}
            {timestamp && (
              <span className="text-[10px] text-muted-foreground">{formatDateTime(timestamp)}</span>
            )}

            <div className="flex items-center gap-0.5 ml-auto">
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy}>
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
              {onRegenerate && (
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onRegenerate}>
                  <RefreshCw className="h-3 w-3" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className={cn('h-7 w-7', feedback === 'up' && 'text-emerald-500')}
                onClick={() => setFeedback('up')}
              >
                <ThumbsUp className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={cn('h-7 w-7', feedback === 'down' && 'text-red-500')}
                onClick={() => setFeedback('down')}
              >
                <ThumbsDown className="h-3 w-3" />
              </Button>
              {(reason || sources?.length || explainability || warning) && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => setShowDetails(!showDetails)}
                >
                  <Brain className="h-3 w-3" />
                  Explain
                  <ChevronDown className={cn('h-3 w-3 transition-transform', showDetails && 'rotate-180')} />
                </Button>
              )}
            </div>
          </div>
        )}

        <AnimatePresence>
          {showDetails && !isUser && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="w-full space-y-3"
            >
              {warning && (
                <Card className="border-amber-500/30 bg-amber-500/5">
                  <CardContent className="flex items-start gap-2 p-3">
                    <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-600 dark:text-amber-400">{warning}</p>
                  </CardContent>
                </Card>
              )}
              {reason && (
                <Card className="border-primary/20">
                  <CardContent className="p-3">
                    <p className="text-xs font-medium mb-1 flex items-center gap-1">
                      <Brain className="h-3 w-3" /> Reasoning
                    </p>
                    <p className="text-xs text-muted-foreground">{reason}</p>
                  </CardContent>
                </Card>
              )}
              {sources && sources.length > 0 && (
                <Card>
                  <CardContent className="p-3">
                    <p className="text-xs font-medium mb-2 flex items-center gap-1">
                      <BookOpen className="h-3 w-3" /> Retrieved Context
                    </p>
                    <ul className="space-y-1">
                      {sources.map((s, i) => (
                        <li key={i} className="text-xs text-muted-foreground truncate">
                          • {s}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
              {explainability && Object.keys(explainability).length > 0 && (
                <Card>
                  <CardContent className="p-3">
                    <p className="text-xs font-medium mb-2">Explainability</p>
                    <pre className="text-[10px] text-muted-foreground overflow-x-auto">
                      {JSON.stringify(explainability, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
