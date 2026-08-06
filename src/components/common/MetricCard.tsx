import { motion } from 'framer-motion'
import { type LucideIcon, TrendingDown, TrendingUp } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/utils'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: { value: number; label: string }
  gradient?: string
  className?: string
}

export function MetricCard({ title, value, subtitle, icon: Icon, trend, gradient, className }: MetricCardProps) {
  const isPositive = trend && trend.value >= 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className={cn('overflow-hidden transition-all hover:shadow-card-hover', className)}>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <p className="text-3xl font-bold tracking-tight">{value}</p>
              {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
              {trend && (
                <div className={cn('flex items-center gap-1 text-xs font-medium', isPositive ? 'text-emerald-500' : 'text-red-500')}>
                  {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(trend.value)}% {trend.label}
                </div>
              )}
            </div>
            <div className={cn('flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg', gradient || 'from-emerald-500 to-teal-500')}>
              <Icon className="h-6 w-6 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
