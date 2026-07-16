import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { Brain, Loader2, Plus, Search } from 'lucide-react'
import { toast } from 'sonner'
import { useMemories, useCreateMemory } from '@/hooks'
import { PageHeader } from '@/components/layout/PageHeader'
import { MemoryCard } from '@/components/common/MemoryCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Card, CardContent } from '@/components/ui/card'
import { useDebounce } from '@/hooks'
import { formatRelativeDate } from '@/utils'
import type { Memory } from '@/types'

const memorySchema = z.object({
  memory_text: z.string().min(5, 'Memory must be at least 5 characters'),
  category: z.string().min(1, 'Select a category'),
  importance_score: z.coerce.number().min(0).max(1).optional(),
})

type MemoryForm = z.infer<typeof memorySchema>

export function MemoryPage() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [localMemories, setLocalMemories] = useState<Memory[]>([])
  const debouncedSearch = useDebounce(search, 300)

  const { data: apiMemories, isLoading } = useMemories(categoryFilter === 'all' ? undefined : categoryFilter)
  const createMemory = useCreateMemory()

  const memories = [...(apiMemories ?? []), ...localMemories]

  const filtered = memories.filter((m) => {
    const matchesSearch = m.memory_text.toLowerCase().includes(debouncedSearch.toLowerCase())
    const matchesCategory = categoryFilter === 'all' || m.category === categoryFilter
    return matchesSearch && matchesCategory
  })

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<MemoryForm>({
    resolver: zodResolver(memorySchema),
    defaultValues: { importance_score: 0.5 },
  })

  const onSubmit = async (data: MemoryForm) => {
    try {
      await createMemory.mutateAsync(data)
      toast.success('Memory saved')
      setDialogOpen(false)
      reset()
    } catch {
      const newMemory: Memory = {
        id: crypto.randomUUID(),
        memory_text: data.memory_text,
        category: data.category,
        importance_score: data.importance_score || 0.5,
        created_at: new Date().toISOString(),
      }
      setLocalMemories((prev) => [newMemory, ...prev])
      toast.success('Memory saved locally')
      setDialogOpen(false)
      reset()
    }
  }

  const handleDelete = (id: string) => {
    setLocalMemories((prev) => prev.filter((m) => m.id !== id))
    toast.success('Memory deleted')
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Memory"
        description="AI-retained context and insights across sessions"
        badge="RAG"
        action={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="gradient">
                <Plus className="h-4 w-4" /> Add Memory
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Memory</DialogTitle>
                <DialogDescription>Store important context for future AI conversations</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="space-y-2">
                  <Label>Memory</Label>
                  <Textarea {...register('memory_text')} placeholder="What should the AI remember?" rows={3} />
                  {errors.memory_text && <p className="text-xs text-destructive">{errors.memory_text.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select onValueChange={(v) => setValue('category', v)}>
                    <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="career">Career</SelectItem>
                      <SelectItem value="health">Health</SelectItem>
                      <SelectItem value="finance">Finance</SelectItem>
                      <SelectItem value="general">General</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.category && <p className="text-xs text-destructive">{errors.category.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label>Importance (0-1)</Label>
                  <Input type="number" step="0.1" min="0" max="1" {...register('importance_score')} />
                </div>
                <DialogFooter>
                  <Button type="submit" variant="gradient" disabled={createMemory.isPending}>
                    {createMemory.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Memory'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search memories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="career">Career</SelectItem>
            <SelectItem value="health">Health</SelectItem>
            <SelectItem value="finance">Finance</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <Brain className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No memories found</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((memory, i) => (
              <motion.div
                key={memory.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <MemoryCard memory={memory} onDelete={handleDelete} />
              </motion.div>
            ))}
          </div>

          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold mb-4">Timeline</h3>
              <div className="space-y-4">
                {filtered.map((memory) => (
                  <div key={`tl-${memory.id}`} className="flex items-start gap-4 pl-4 border-l-2 border-primary/30">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 -ml-[21px]">
                      <Brain className="h-3 w-3 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm">{memory.memory_text}</p>
                      <p className="text-xs text-muted-foreground mt-1">{formatRelativeDate(memory.created_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
