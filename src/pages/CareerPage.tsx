import { motion } from 'framer-motion'
import {
  Award,
  BookOpen,
  Briefcase,
  DollarSign,
  Map,
  Target,
  TrendingUp,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { ChartCard } from '@/components/common/ChartCard'
import { StatCard } from '@/components/common/StatCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useMemo } from 'react'
import { useProfile } from '@/hooks'
import { formatCurrency } from '@/utils'
import { buildCareerPageData } from '@/utils/profileInsights'

export function CareerPage() {
  const { data: profile } = useProfile()
  const careerData = useMemo(() => buildCareerPageData(profile), [profile])
  const { skills, roadmap, salaryPrediction, certifications, jobRecommendations, progressData } = careerData

  return (
    <div className="space-y-8">
      <PageHeader
        title="Career Dashboard"
        description="Skills, roadmaps, and career intelligence powered by AI"
        badge="Career"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Career Score"
          value={Math.max(60, Math.round((profile?.career?.current_skills?.length || 0) * 10 + 50))}
          subtitle="Overall readiness"
          icon={Target}
          trend={{ value: 8, label: 'this quarter' }}
          gradient="from-blue-500 to-indigo-500"
        />
        <MetricCard
          title="Skills Tracked"
          value={skills.length}
          subtitle="Across categories"
          icon={BookOpen}
          gradient="from-emerald-500 to-teal-500"
        />
        <MetricCard
          title="Predicted Salary"
          value={salaryPrediction.predicted ? formatCurrency(salaryPrediction.predicted) : 'Set profile' }
          subtitle={`In ${salaryPrediction.timeframe}`}
          icon={DollarSign}
          gradient="from-amber-500 to-orange-500"
        />
        <MetricCard
          title="Job Matches"
          value={Math.max(jobRecommendations.length, 0)}
          subtitle="High compatibility"
          icon={Briefcase}
          gradient="from-purple-500 to-pink-500"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <ChartCard title="Skill Progress" description="Monthly skill growth and project count">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={progressData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="month" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="skills" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Skills" />
                <Bar dataKey="projects" fill="#10b981" radius={[4, 4, 0, 0]} name="Projects" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Map className="h-4 w-4 text-primary" />
                Career Roadmap
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {roadmap.map((phase, i) => (
                <motion.div
                  key={phase.phase}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="relative pl-6 border-l-2 border-primary/30"
                >
                  <div className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-primary" />
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold">{phase.phase}</h4>
                    <Badge variant="secondary" className="text-[10px]">{phase.duration}</Badge>
                  </div>
                  <ul className="space-y-1">
                    {phase.tasks.map((task) => (
                      <li key={task} className="text-sm text-muted-foreground flex items-center gap-2">
                        <span className="h-1 w-1 rounded-full bg-primary" />
                        {task}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Skills</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {skills.map((skill) => (
                <div key={skill.name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{skill.name}</span>
                    <span className="text-xs text-muted-foreground">{skill.level}%</span>
                  </div>
                  <Progress value={skill.level} className="h-1.5" />
                  <Badge variant="outline" className="text-[10px] mt-1">{skill.category}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Award className="h-4 w-4 text-primary" />
                Certifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {certifications.map((cert) => (
                <div key={cert} className="flex items-center gap-2 rounded-lg bg-secondary/50 p-3">
                  <Award className="h-4 w-4 text-amber-500 shrink-0" />
                  <span className="text-sm">{cert}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Current Salary"
          value={formatCurrency(salaryPrediction.current)}
          icon={DollarSign}
          iconColor="text-blue-500"
        />
        <StatCard
          label="Target Role"
          value="Data Scientist"
          change="+41% growth potential"
          icon={TrendingUp}
          iconColor="text-emerald-500"
        />
        <StatCard
          label="Resume Tips"
          value="3 suggestions"
          change="Update ML projects section"
          icon={BookOpen}
          iconColor="text-purple-500"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Job Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            {jobRecommendations.map((job) => (
              <motion.div
                key={job.title}
                whileHover={{ y: -2 }}
                className="rounded-xl border p-4 transition-shadow hover:shadow-card-hover"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{job.title}</h4>
                  <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                    {job.match}% match
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{job.company}</p>
                <Progress value={job.match} className="mt-3 h-1" />
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
