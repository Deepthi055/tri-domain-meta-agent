import { useState } from 'react'
import { Loader2, Plus, FileText } from 'lucide-react'
import { toast } from 'sonner'
import { useReports, useCreateReport } from '@/hooks'
import { reportService, getErrorMessage } from '@/services'
import { PageHeader } from '@/components/layout/PageHeader'
import { ReportCard } from '@/components/common/ReportCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
export function ReportsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [domain, setDomain] = useState('career')
  const [generating, setGenerating] = useState<string | null>(null)

  const { data: apiReports, isLoading } = useReports()
  const createReport = useCreateReport()

  const reports = apiReports ?? []

  const handleGenerate = async () => {
    setGenerating('new')
    try {
      await createReport.mutateAsync({ domain })
      toast.success('Report generated successfully')
      setDialogOpen(false)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setGenerating(null)
    }
  }

  const handleDownload = async (id: string) => {
    try {
      const blob = await reportService.download(id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Report downloaded')
    } catch {
      toast.info('Download will be available when backend is connected')
    }
  }

  const handlePreview = (id: string) => {
    toast.info(`Preview for report ${id.slice(0, 8)}...`)
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reports"
        description="Generate and download AI advisory reports"
        action={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="gradient">
                <Plus className="h-4 w-4" /> Generate Report
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Generate New Report</DialogTitle>
                <DialogDescription>
                  Create a comprehensive advisory report for a specific domain
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Domain</Label>
                  <Select value={domain} onValueChange={setDomain}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="career">Career Advisory</SelectItem>
                      <SelectItem value="health">Health Advisory</SelectItem>
                      <SelectItem value="finance">Finance Advisory</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="gradient" onClick={handleGenerate} disabled={generating === 'new'}>
                  {generating === 'new' ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Generate'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : reports.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">No reports generated yet</p>
            <Button variant="gradient" onClick={() => setDialogOpen(true)}>
              Generate your first report
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {reports.map((report) => (
            <ReportCard
              key={report.id}
              report={report}
              onDownload={handleDownload}
              onPreview={handlePreview}
            />
          ))}
        </div>
      )}
    </div>
  )
}
