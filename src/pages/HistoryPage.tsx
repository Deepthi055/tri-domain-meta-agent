import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { History, Loader2, Search, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { useChatHistory } from '@/hooks'
import { PageHeader } from '@/components/layout/PageHeader'
import { ConversationCard } from '@/components/common/ConversationCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useDebounce } from '@/hooks'
import { ROUTES } from '@/utils/constants'
import type { ConversationSummary } from '@/types'

export function HistoryPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [domainFilter, setDomainFilter] = useState('all')
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set())
  const debouncedSearch = useDebounce(search, 300)

  const { data: apiHistory, isLoading } = useChatHistory()
  const conversations = (apiHistory ?? []).filter(
    (c) => !deletedIds.has(c.id)
  )

  const filtered = conversations.filter((c) => {
    const matchesDomain = domainFilter === 'all' || c.domain === domainFilter
    const matchesSearch =
      c.id.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
      c.domain.toLowerCase().includes(debouncedSearch.toLowerCase())
    return matchesDomain && matchesSearch
  })

  const handleDelete = (id: string) => {
    setDeletedIds((prev) => new Set([...prev, id]))
    toast.success('Conversation removed')
  }

  const handleOpen = (conv: ConversationSummary) => {
    navigate(ROUTES.CHAT, { state: { conversationId: conv.id } })
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="History"
        description="Browse and manage your past AI conversations"
      />

      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Tabs value={domainFilter} onValueChange={setDomainFilter}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="career">Career</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
            <TabsTrigger value="finance">Finance</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <History className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No conversations found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((conv) => (
            <div key={conv.id} className="group flex items-center gap-2">
              <div className="flex-1">
                <ConversationCard
                  conversation={conv}
                  onClick={() => handleOpen(conv)}
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleDelete(conv.id)}
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
