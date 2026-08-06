import { motion } from 'framer-motion'
import { MessageSquare, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatRelativeDate } from '@/utils'
import type { ConversationSummary } from '@/types'

interface ConversationCardProps {
  conversation: ConversationSummary
  onClick?: () => void
  onDelete?: () => void
  isActive?: boolean
}

export function ConversationCard({ conversation, onClick, onDelete, isActive }: ConversationCardProps) {
  return (
    <motion.div whileHover={{ x: 2 }} transition={{ duration: 0.15 }}>
      <Card
        className={`cursor-pointer transition-all hover:shadow-md ${isActive ? 'border-primary bg-primary/5' : ''}`}
        onClick={onClick}
      >
        <CardContent className="flex items-center gap-3 p-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={conversation.domain as 'career' | 'health' | 'finance'} className="text-[10px] capitalize">
                {conversation.domain}
              </Badge>
              <span className="text-xs text-muted-foreground">{formatRelativeDate(conversation.created_at)}</span>
            </div>
            <p className="text-sm font-medium truncate">Conversation #{conversation.id.slice(0, 8)}</p>
          </div>
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0 opacity-0 group-hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation()
                onDelete()
              }}
            >
              <Trash2 className="h-4 w-4 text-muted-foreground" />
            </Button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
