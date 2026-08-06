import { motion } from 'framer-motion'
import { Download, FileText, Eye } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatDate } from '@/utils'
import type { Report } from '@/types'

interface ReportCardProps {
  report: Report
  onDownload?: (id: string) => void
  onPreview?: (id: string) => void
  status?: 'ready' | 'generating' | 'failed'
}

export function ReportCard({ report, onDownload, onPreview, status = 'ready' }: ReportCardProps) {
  const domain = report.report_name.toLowerCase().includes('career')
    ? 'career'
    : report.report_name.toLowerCase().includes('health')
      ? 'health'
      : report.report_name.toLowerCase().includes('finance')
        ? 'finance'
        : 'default'

  return (
    <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
      <Card className="group">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold truncate">{report.report_name}</h3>
                {domain !== 'default' && (
                  <Badge variant={domain as 'career' | 'health' | 'finance'} className="text-[10px] capitalize shrink-0">
                    {domain}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Generated {formatDate(report.generated_at)}
              </p>
              <div className="flex items-center gap-2">
                <Badge
                  variant={status === 'ready' ? 'secondary' : status === 'generating' ? 'outline' : 'destructive'}
                  className="text-[10px]"
                >
                  {status === 'ready' ? 'Ready' : status === 'generating' ? 'Generating...' : 'Failed'}
                </Badge>
                {status === 'ready' && (
                  <>
                    {onPreview && (
                      <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => onPreview(report.id)}>
                        <Eye className="h-3 w-3 mr-1" /> Preview
                      </Button>
                    )}
                    {onDownload && (
                      <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => onDownload(report.id)}>
                        <Download className="h-3 w-3 mr-1" /> PDF
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
