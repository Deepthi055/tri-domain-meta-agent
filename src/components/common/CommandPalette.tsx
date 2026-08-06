import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Briefcase,
  Heart,
  History,
  LayoutDashboard,
  MessageSquare,
  Settings,
  User,
  Wallet,
  Brain,
  FileText,
} from 'lucide-react'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { ROUTES } from '@/utils/constants'

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const pages = [
  { name: 'Dashboard', href: ROUTES.DASHBOARD, icon: LayoutDashboard },
  { name: 'Ask AI', href: ROUTES.CHAT, icon: MessageSquare },
  { name: 'Career', href: ROUTES.CAREER, icon: Briefcase },
  { name: 'Health', href: ROUTES.HEALTH, icon: Heart },
  { name: 'Finance', href: ROUTES.FINANCE, icon: Wallet },
  { name: 'Profile', href: ROUTES.PROFILE, icon: User },
  { name: 'Memory', href: ROUTES.MEMORY, icon: Brain },
  { name: 'Reports', href: ROUTES.REPORTS, icon: FileText },
  { name: 'History', href: ROUTES.HISTORY, icon: History },
  { name: 'Settings', href: ROUTES.SETTINGS, icon: Settings },
]

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate()

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        onOpenChange(!open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [open, onOpenChange])

  const run = (href: string) => {
    onOpenChange(false)
    navigate(href)
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Search pages and actions..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Pages">
          {pages.map((page) => (
            <CommandItem key={page.href} onSelect={() => run(page.href)}>
              <page.icon className="mr-2 h-4 w-4" />
              {page.name}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Quick Actions">
          <CommandItem onSelect={() => run(ROUTES.CHAT)}>
            <MessageSquare className="mr-2 h-4 w-4" />
            New AI Conversation
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
