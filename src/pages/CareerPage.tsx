import {
  BookOpen,
  DollarSign,
  TrendingUp,
} from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { StatCard } from '@/components/common/StatCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useMemo } from 'react'
import { useCareerAssessment, useProfile } from '@/hooks'
import { getErrorMessage } from '@/services'
import { formatCurrency } from '@/utils'
import { buildCareerPageData } from '@/utils/profileInsights'

export function CareerPage() {
  const { data: profile } = useProfile()
  const careerAssessment = useCareerAssessment()
  const careerData = useMemo(() => buildCareerPageData(profile), [profile])
  const { skills, currentSalary } = careerData
  const targetRoleLabel = profile?.career?.target_role || 'Set target role'
  const targetRoleChange = profile?.career?.target_role
    ? `Progress toward ${profile.career.target_role}`
    : 'Add a target role for tailored recommendations'
  const resumeTip = profile?.career?.resume
    ? `Update resume with ${profile?.career?.target_role || 'career'} achievements`
    : 'Add your resume summary to improve guidance'

  return (
    <div className="space-y-8">
      <PageHeader
        title="Career Dashboard"
        description="Skills, roadmaps, and career intelligence powered by AI"
        badge="Career"
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <MetricCard
          title="Skills Tracked"
          value={skills.length}
          subtitle="Saved current skills"
          icon={BookOpen}
          gradient="from-emerald-500 to-teal-500"
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div>
            <CardTitle className="text-base">Target-Role Skill Match</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">Check your saved skills against your target role.</p>
          </div>
          <Button
            variant="gradient"
            onClick={() => careerAssessment.mutate()}
            disabled={careerAssessment.isPending}
          >
            {careerAssessment.isPending ? 'Checking...' : 'Check Skill Match'}
          </Button>
        </CardHeader>
        <CardContent>
          {careerAssessment.isError && (
            <p className="text-sm text-destructive">{getErrorMessage(careerAssessment.error)}</p>
          )}
          {careerAssessment.data && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Target Role</p>
                <p className="font-semibold capitalize">{careerAssessment.data.target_role}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Skill Match</p>
                <p className="text-xl font-bold">{careerAssessment.data.value}%</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Matched Skills</p>
                <p className="text-sm">{careerAssessment.data.details.matched_skills.join(', ') || 'None'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Missing Skills</p>
                <p className="text-sm">{careerAssessment.data.details.missing_skills.join(', ') || 'None'}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Skill Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Skill progress history will appear when real assessment history is available.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Career Roadmap</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Career roadmap will appear when personalized career planning is available.</p>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Skills</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {skills.length > 0 ? skills.map((skill) => (
                <p key={skill} className="text-sm font-medium">{skill}</p>
              )) : (
                <p className="text-sm text-muted-foreground">Add current skills to see them here.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {currentSalary !== null ? (
          <StatCard
            label="Current Salary"
            value={formatCurrency(currentSalary)}
            icon={DollarSign}
            iconColor="text-blue-500"
          />
        ) : null}
        <StatCard
          label="Target Role"
          value={targetRoleLabel}
          change={targetRoleChange}
          icon={TrendingUp}
          iconColor="text-emerald-500"
        />
        <StatCard
          label="Resume Tips"
          value={resumeTip}
          change={profile?.career?.resume ? 'Resume profile detected' : 'Complete your profile'}
          icon={BookOpen}
          iconColor="text-purple-500"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Job Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Job recommendations will appear when a real recommendations source is available.</p>
        </CardContent>
      </Card>
    </div>
  )
}
