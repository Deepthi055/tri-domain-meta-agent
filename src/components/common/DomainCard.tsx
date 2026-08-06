import { motion } from 'framer-motion'
import { ArrowRight, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { DOMAIN_COLORS } from '@/utils/constants'
import { cn } from '@/utils'

interface DomainCardProps {
  domain: 'career' | 'health' | 'finance'
  title: string
  description: string
  score: number
  icon: LucideIcon
  href: string
  insight?: string
}

export function DomainCard({ domain, title, description, score, icon: Icon, href, insight }: DomainCardProps) {
  const colors = DOMAIN_COLORS[domain]

  return (
    <motion.div whileHover={{ y: -4 }} transition={{ duration: 0.2 }}>
      <Link to={href}>
        <Card className={cn('group overflow-hidden border transition-all hover:shadow-card-hover', colors.border)}>
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className={cn('flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br', colors.gradient)}>
                <Icon className="h-5 w-5 text-white" />
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold">{score}</span>
                <span className="text-sm text-muted-foreground">/100</span>
              </div>
            </div>
            <h3 className="font-semibold mb-1">{title}</h3>
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{description}</p>
            <Progress value={score} className="mb-3 h-1.5" />
            {insight && (
              <p className="text-xs text-muted-foreground italic line-clamp-2">{insight}</p>
            )}
            <div className="mt-4 flex items-center text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
              Explore <ArrowRight className="ml-1 h-4 w-4" />
            </div>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  )
}
