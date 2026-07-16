import { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Send, Plus, Sparkles, Zap, GitCompare } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/contexts/AuthContext'
import { useProfile, useChatHistory, useConversation, useSendChat, useQueryMutation, useLangchainQuery } from '@/hooks'
import { getErrorMessage } from '@/services'
import { PageHeader } from '@/components/layout/PageHeader'
import { AIResponseCard } from '@/components/common/AIResponseCard'
import { ConversationCard } from '@/components/common/ConversationCard'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { SUGGESTED_PROMPTS } from '@/utils/constants'
import type { ChatResponse, QueryRequest, QueryResponse } from '@/types'

interface LocalMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  domain?: string
  confidence?: number | null
  reason?: string | null
  sources?: string[]
  warning?: string
}

export function ChatPage() {
  const { user } = useAuth()
  const location = useLocation()
  const scrollRef = useRef<HTMLDivElement>(null)

  const [messages, setMessages] = useState<LocalMessage[]>([])
  const [input, setInput] = useState('')
  const [domain, setDomain] = useState<string>('auto')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [agentMode, setAgentMode] = useState<'standard' | 'langchain'>('standard')
  const [compareMode, setCompareMode] = useState(false)
  const [comparison, setComparison] = useState<{
    standard?: QueryResponse & { executionTime: number }
    langchain?: QueryResponse & { executionTime: number }
  } | null>(null)

  const { data: profile } = useProfile()
  const { data: history } = useChatHistory()
  const { data: conversation } = useConversation(conversationId)
  const sendChat = useSendChat()
  const queryMutation = useQueryMutation()
  const langchainQuery = useLangchainQuery()

  const conversations = history ?? []

  useEffect(() => {
    const state = location.state as { query?: string; conversationId?: string } | null
    if (state?.query) {
      setInput(state.query)
      window.history.replaceState({}, '')
    }
    if (state?.conversationId) {
      setConversationId(state.conversationId)
      window.history.replaceState({}, '')
    }
  }, [location.state])

  useEffect(() => {
    if (conversation?.messages) {
      setMessages(
        conversation.messages.map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: m.timestamp,
          domain: conversation.domain,
        }))
      )
    }
  }, [conversation])

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  const buildQueryRequest = (query: string): QueryRequest => ({
    name: user?.name || 'User',
    age: profile?.general?.age || 25,
    query,
    domain: domain === 'auto' ? undefined : domain,
    current_skills: profile?.career?.current_skills,
    target_role: profile?.career?.target_role,
    experience_level: profile?.career?.experience_level,
    location: profile?.general?.location,
    weight_kg: profile?.general?.weight_kg,
    height_cm: profile?.general?.height_cm,
    fitness_goal: profile?.health?.fitness_goal,
    sleep_hours: profile?.health?.sleep_hours,
    monthly_income: profile?.finance?.monthly_income,
    monthly_expenses: profile?.finance?.monthly_expenses,
    risk_tolerance: profile?.finance?.risk_appetite,
  })

  const handleSend = async (text?: string) => {
    const query = (text || input).trim()
    if (!query || isStreaming) return

    const userMsg: LocalMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsStreaming(true)
    setComparison(null)

    try {
      if (compareMode) {
        const req = buildQueryRequest(query)
        const [stdResult, lcResult] = await Promise.all([
          (async () => {
            const start = performance.now()
            const res = await queryMutation.mutateAsync(req)
            return { ...res, executionTime: performance.now() - start }
          })(),
          (async () => {
            const start = performance.now()
            const res = await langchainQuery.mutateAsync(req)
            return { ...res, executionTime: performance.now() - start }
          })(),
        ])
        setComparison({ standard: stdResult, langchain: lcResult })

        const answer = stdResult.responses?.[0]?.recommendation || stdResult.message || 'No response'
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: answer,
            timestamp: new Date().toISOString(),
            domain: stdResult.responses?.[0]?.domain || domain,
            confidence: stdResult.responses?.[0]?.confidence,
            reason: stdResult.responses?.[0]?.reason,
            warning: stdResult.warning,
          },
        ])
      } else if (agentMode === 'langchain') {
        const start = performance.now()
        const res = await langchainQuery.mutateAsync(buildQueryRequest(query))
        const elapsed = performance.now() - start

        const answer = res.responses?.[0]?.recommendation || res.message || 'No response'
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: answer + `\n\n*Response time: ${elapsed.toFixed(0)}ms*`,
            timestamp: new Date().toISOString(),
            domain: res.responses?.[0]?.domain || domain,
            confidence: res.responses?.[0]?.confidence,
            reason: res.responses?.[0]?.reason,
            warning: res.warning,
          },
        ])
      } else {
        const res: ChatResponse = await sendChat.mutateAsync({
          query,
          domain: domain === 'auto' ? 'auto' : domain,
          conversation_id: conversationId,
        })
        if (!conversationId) setConversationId(res.conversation_id)

        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: res.answer,
            timestamp: new Date().toISOString(),
            domain: res.domain,
            confidence: res.confidence,
            reason: res.reason,
            sources: res.sources,
          },
        ])
      }
    } catch (err) {
      toast.error(getErrorMessage(err))
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setIsStreaming(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setConversationId(null)
    setComparison(null)
  }

  const renderComparisonPanel = () => {
    if (!comparison) return null
    const panels = [
      { label: 'Standard Meta-Agent', data: comparison.standard },
      { label: 'LangChain Agent', data: comparison.langchain },
    ]

    return (
      <div className="grid gap-4 md:grid-cols-2 mb-4">
        {panels.map(({ label, data }) => (
          <Card key={label} className="border-primary/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold">{label}</h4>
                <Badge variant="secondary" className="text-[10px]">
                  {data?.executionTime?.toFixed(0)}ms
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mb-2">
                Confidence: {data?.responses?.[0]?.confidence ? `${Math.round(data.responses[0].confidence * 100)}%` : 'N/A'}
              </p>
              <p className="text-sm">{data?.responses?.[0]?.recommendation || data?.message || 'No response'}</p>
              {data?.responses?.[0]?.reason && (
                <p className="text-xs text-muted-foreground mt-2 italic">{data.responses[0].reason}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      <div className="hidden lg:flex w-72 flex-col rounded-xl border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-sm font-semibold">Conversations</h3>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleNewChat}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <ScrollArea className="flex-1 p-3 space-y-2">
          {conversations.map((conv) => (
            <ConversationCard
              key={conv.id}
              conversation={conv}
              isActive={conv.id === conversationId}
              onClick={() => setConversationId(conv.id)}
            />
          ))}
        </ScrollArea>
      </div>

      <div className="flex flex-1 flex-col rounded-xl border bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="flex items-center justify-between border-b px-4 py-3 gap-4 flex-wrap">
          <PageHeader title="Ask AI" description="Multi-domain advisory assistant" className="!flex-row !gap-2" />

          <div className="flex items-center gap-4 flex-wrap">
            <Tabs value={domain} onValueChange={setDomain}>
              <TabsList className="h-8">
                <TabsTrigger value="auto" className="text-xs px-2">Auto</TabsTrigger>
                <TabsTrigger value="career" className="text-xs px-2">Career</TabsTrigger>
                <TabsTrigger value="health" className="text-xs px-2">Health</TabsTrigger>
                <TabsTrigger value="finance" className="text-xs px-2">Finance</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-2">
              <Switch
                id="agent-mode"
                checked={agentMode === 'langchain'}
                onCheckedChange={(c) => setAgentMode(c ? 'langchain' : 'standard')}
              />
              <Label htmlFor="agent-mode" className="text-xs flex items-center gap-1 cursor-pointer">
                {agentMode === 'langchain' ? <Zap className="h-3 w-3" /> : <Sparkles className="h-3 w-3" />}
                {agentMode === 'langchain' ? 'LangChain' : 'Standard'}
              </Label>
            </div>

            <div className="flex items-center gap-2">
              <Switch id="compare" checked={compareMode} onCheckedChange={setCompareMode} />
              <Label htmlFor="compare" className="text-xs flex items-center gap-1 cursor-pointer">
                <GitCompare className="h-3 w-3" /> Compare
              </Label>
            </div>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-12">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center max-w-lg"
              >
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 shadow-glow">
                  <Sparkles className="h-8 w-8 text-white" />
                </div>
                <h2 className="text-xl font-bold mb-2">How can I help you today?</h2>
                <p className="text-muted-foreground mb-8">
                  Ask about career growth, health goals, or financial planning
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {SUGGESTED_PROMPTS.slice(0, 4).map((prompt) => (
                    <Button
                      key={prompt.text}
                      variant="outline"
                      className="h-auto py-3 px-4 text-left justify-start text-xs whitespace-normal"
                      onClick={() => handleSend(prompt.text)}
                    >
                      {prompt.text}
                    </Button>
                  ))}
                </div>
              </motion.div>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto">
              {renderComparisonPanel()}
              {messages.map((msg) => (
                <AIResponseCard
                  key={msg.id}
                  content={msg.content}
                  role={msg.role}
                  timestamp={msg.timestamp}
                  domain={msg.domain}
                  confidence={msg.confidence}
                  reason={msg.reason}
                  sources={msg.sources}
                  warning={msg.warning}
                  onRegenerate={msg.role === 'assistant' ? () => {
                    const lastUser = [...messages].reverse().find((m) => m.role === 'user')
                    if (lastUser) handleSend(lastUser.content)
                  } : undefined}
                />
              ))}
              {isStreaming && (
                <AIResponseCard content="" role="assistant" isStreaming />
              )}
              <div ref={scrollRef} />
            </div>
          )}
        </ScrollArea>

        <div className="border-t p-4">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <Textarea
              placeholder="Ask about career, health, or finance..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              className="min-h-[44px] max-h-32 resize-none"
              rows={1}
            />
            <Button
              variant="gradient"
              size="icon"
              className="shrink-0 h-11 w-11"
              onClick={() => handleSend()}
              disabled={!input.trim() || isStreaming}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
