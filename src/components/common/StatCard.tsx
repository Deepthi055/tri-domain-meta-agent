import { motion } from 'framer-motion'
import { type LucideIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/utils'

interface StatCardProps {
  label: string
  value: string | number
  change?: string
  icon: LucideIcon
  iconColor?: string
  className?: string
}

export function StatCard({ label, value, change, icon: Icon, iconColor, className }: StatCardProps) {
  return (
    <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.2 }}>
      <Card className={cn('glass', className)}>
        <CardContent className="flex items-center gap-4 p-5">
          <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg bg-secondary', iconColor)}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-xl font-bold">{value}</p>
            {change && <p className="text-xs text-emerald-500">{change}</p>}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
