import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronLeft, LogOut } from 'lucide-react'
import { cn } from '@/utils'
import { mainNavItems, secondaryNavItems } from '@/utils/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation()
  const { logout } = useAuth()

  const NavLink = ({ href, icon: Icon, title, badge }: { href: string; icon: React.ComponentType<{ className?: string }>; title: string; badge?: string }) => {
    const isActive = location.pathname === href || location.pathname.startsWith(href + '/')

    const link = (
      <Link
        to={href}
        className={cn(
          'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
          isActive
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
        )}
      >
        {isActive && (
          <motion.div
            layoutId="sidebar-active"
            className="absolute inset-0 rounded-lg bg-primary/10"
            transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
          />
        )}
        <Icon className={cn('relative h-4 w-4 shrink-0', isActive && 'text-primary')} />
        {!collapsed && (
          <>
            <span className="relative flex-1">{title}</span>
            {badge && (
              <span className="relative rounded-md bg-primary/20 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                {badge}
              </span>
            )}
          </>
        )}
      </Link>
    )

    if (collapsed) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>{link}</TooltipTrigger>
          <TooltipContent side="right">{title}</TooltipContent>
        </Tooltip>
      )
    }

    return link
  }

  return (
    <TooltipProvider delayDuration={0}>
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 260 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="fixed left-0 top-0 z-40 flex h-screen flex-col border-r bg-card/50 backdrop-blur-xl"
      >
        <div className="flex h-16 items-center gap-3 border-b px-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 shadow-glow">
            <span className="text-sm font-bold text-white">TD</span>
          </div>
          {!collapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-w-0">
              <p className="truncate text-sm font-bold">TriDomain</p>
              <p className="truncate text-[10px] text-muted-foreground">Meta-Agent</p>
            </motion.div>
          )}
        </div>

        <ScrollArea className="flex-1 px-3 py-4">
          <div className="space-y-1">
            {mainNavItems.map((item) => (
              <NavLink key={item.href} {...item} />
            ))}
          </div>

          <Separator className="my-4" />

          <div className="space-y-1">
            {secondaryNavItems.map((item) => (
              <NavLink key={item.href} {...item} />
            ))}
          </div>
        </ScrollArea>

        <div className="border-t p-3 space-y-2">
          <Button
            variant="ghost"
            size={collapsed ? 'icon' : 'default'}
            className={cn('w-full text-muted-foreground', !collapsed && 'justify-start')}
            onClick={logout}
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && <span>Logout</span>}
          </Button>
          <Button variant="ghost" size="icon" className="w-full" onClick={onToggle}>
            <ChevronLeft className={cn('h-4 w-4 transition-transform', collapsed && 'rotate-180')} />
          </Button>
        </div>
      </motion.aside>
    </TooltipProvider>
  )
}

export function getSidebarWidth(collapsed: boolean) {
  return collapsed ? 72 : 260
}
