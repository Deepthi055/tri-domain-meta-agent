import { motion } from 'framer-motion'
import { Brain, Trash2, Star } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { formatRelativeDate } from '@/utils'
import type { Memory } from '@/types'

interface MemoryCardProps {
  memory: Memory
  onDelete?: (id: string) => void
}

export function MemoryCard({ memory, onDelete }: MemoryCardProps) {
  const importance = Math.round(memory.importance_score * 100)

  return (
    <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
      <Card className="group overflow-hidden">
        <CardContent className="p-5">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Brain className="h-4 w-4 text-primary" />
              </div>
              <Badge variant={memory.category as 'career' | 'health' | 'finance'} className="text-[10px] capitalize">
                {memory.category}
              </Badge>
            </div>
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => onDelete(memory.id)}
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              </Button>
            )}
          </div>

          <p className="text-sm leading-relaxed mb-4">{memory.memory_text}</p>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Star className="h-3 w-3 text-amber-500" />
              <span className="text-xs text-muted-foreground">Importance</span>
              <Progress value={importance} className="w-16 h-1" />
              <span className="text-xs font-medium">{importance}%</span>
            </div>
            <span className="text-xs text-muted-foreground">{formatRelativeDate(memory.created_at)}</span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
