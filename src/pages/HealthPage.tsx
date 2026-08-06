import { motion } from 'framer-motion'
import {
  Activity,
  Droplets,
  Flame,
  Heart,
  Moon,
  Scale,
  Utensils,
  Dumbbell,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { ChartCard } from '@/components/common/ChartCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProfile } from '@/hooks'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/utils/constants'
import { calculateDomainScores, buildHealthPageData } from '@/utils/profileInsights'

export function HealthPage() {
  const { data: profile, isLoading: isProfileLoading } = useProfile()
  const navigate = useNavigate()
  const healthData = useMemo(() => buildHealthPageData(profile), [profile])
  const { bmi, bmiStatus, sleep, stress, calories, water, weeklyActivity, dietSuggestions, workoutSuggestions } = healthData
  const domainScores = useMemo(() => calculateDomainScores(profile), [profile])
  const hasHealthData = Boolean(
    profile?.general?.height_cm ||
    profile?.general?.weight_kg ||
    profile?.health?.medical_conditions ||
    profile?.health?.lifestyle ||
    profile?.health?.fitness_goal ||
    profile?.health?.sleep_hours ||
    profile?.health?.sleep_quality ||
    profile?.health?.diet_preference ||
    profile?.health?.workout ||
    profile?.health?.health_goals ||
    profile?.health?.water_intake,
  )

  const bmiColor = bmi < 25 ? 'text-emerald-500' : 'text-amber-500'

  if (isProfileLoading) {
    return (
      <div className="space-y-8">
        <PageHeader title="Health Dashboard" description="Loading profile..." />
        <div className="flex justify-center py-12"><div className="loader" /></div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="space-y-8">
        <PageHeader title="Health Dashboard" description="Complete your profile to see health insights" badge="Profile Needed" />
        <Card>
          <CardContent className="p-8 text-center">
            <h3 className="text-lg font-semibold mb-2">No health profile</h3>
            <p className="text-sm text-muted-foreground mb-4">Provide basic health details to view personalized BMI, sleep, and workout recommendations.</p>
            <Button variant="gradient" onClick={() => navigate(ROUTES.PROFILE)}>Edit Profile</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Health Dashboard"
        description="Fitness, nutrition, and wellness tracking"
        badge="Health"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Health Score"
          value={domainScores.health}
          subtitle="Overall wellness"
          icon={Heart}
          trend={hasHealthData ? { value: domainScores.health, label: 'profile completion' } : undefined}
          gradient="from-emerald-500 to-teal-500"
        />
        <MetricCard
          title="BMI"
          value={bmi}
          subtitle={bmiStatus}
          icon={Scale}
          gradient="from-blue-500 to-cyan-500"
        />
        <MetricCard
          title="Sleep"
          value={sleep.hours !== null ? `${sleep.hours}h` : 'No data available'}
          subtitle={sleep.quality !== null ? `Quality: ${sleep.quality}/10` : 'Complete your profile'}
          icon={Moon}
          gradient="from-indigo-500 to-purple-500"
        />
        <MetricCard
          title="Stress Level"
          value={stress.level !== null ? `${stress.level}/10` : 'No data available'}
          subtitle={stress.level !== null ? stress.trend : 'Complete your profile'}
          icon={Activity}
          gradient="from-rose-500 to-pink-500"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">BMI Analysis</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <div className="relative h-40 w-40">
              <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
                <circle cx="50" cy="50" r="40" fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
                {bmi > 0 && (
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="url(#bmiGrad)"
                    strokeWidth="8"
                    strokeDasharray={`${(bmi / 40) * 251} 251`}
                    strokeLinecap="round"
                  />
                )}
                <defs>
                  <linearGradient id="bmiGrad">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="100%" stopColor="#14b8a6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold">{bmi > 0 ? bmi : '—'}</span>
                <span className={`text-xs font-medium ${bmiColor}`}>{bmiStatus}</span>
              </div>
            </div>
            <p className="text-sm text-muted-foreground text-center mt-4">
              {bmi > 0 ? 'Healthy BMI range: 18.5 – 24.9' : 'No information available. Complete your profile to calculate BMI.'}
            </p>
          </CardContent>
        </Card>

        <ChartCard title="Weekly Activity" description="Steps and workout minutes" className="lg:col-span-2">
          {weeklyActivity.length ? (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={weeklyActivity}>
              <defs>
                <linearGradient id="stepsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="day" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
              <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Area type="monotone" dataKey="steps" stroke="#10b981" fill="url(#stepsGrad)" strokeWidth={2} />
              <Line type="monotone" dataKey="workout" stroke="#14b8a6" strokeWidth={2} dot={{ r: 4 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="No information available. Complete your profile to see activity trends." />
          )}
        </ChartCard>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10">
                <Flame className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Calories</p>
                <p className="text-xl font-bold">
                  {calories.consumed !== null && calories.target !== null ? `${calories.consumed} / ${calories.target}` : 'No information available'}
                </p>
              </div>
            </div>
            {calories.consumed !== null && calories.target !== null ? (
              <Progress value={(calories.consumed / calories.target) * 100} className="h-2 mb-2" />
            ) : (
              <div className="h-2 mb-2 rounded-full bg-muted" />
            )}
            <p className="text-xs text-muted-foreground">
              {calories.burned !== null ? `Burned: ${calories.burned} kcal today` : 'Complete your profile to track calories'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10">
                <Droplets className="h-5 w-5 text-cyan-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Water Intake</p>
                <p className="text-xl font-bold">
                  {water.glasses !== null && water.target !== null ? `${water.glasses} / ${water.target} glasses` : 'No information available'}
                </p>
              </div>
            </div>
            {water.glasses !== null && water.target !== null ? (
              <Progress value={(water.glasses / water.target) * 100} className="h-2" />
            ) : (
              <div className="h-2 rounded-full bg-muted" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10">
                <Moon className="h-5 w-5 text-indigo-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sleep Quality</p>
                <p className="text-xl font-bold">{sleep.quality !== null ? `${sleep.quality}/10` : 'No information available'}</p>
              </div>
            </div>
            {sleep.quality !== null && <Badge variant="secondary" className="text-[10px] capitalize">{sleep.trend}</Badge>}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Utensils className="h-4 w-4 text-primary" />
              Diet Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dietSuggestions.map((tip, i) => (
              <motion.div
                key={tip}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-3 rounded-lg bg-secondary/50 p-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-xs font-bold text-emerald-500">
                  {i + 1}
                </span>
                <p className="text-sm">{tip}</p>
              </motion.div>
            ))}
            {!dietSuggestions.length && <EmptyState text="No information available. Complete your profile to receive diet guidance." />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Dumbbell className="h-4 w-4 text-primary" />
              Workout Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {workoutSuggestions.map((tip, i) => (
              <motion.div
                key={tip}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-3 rounded-lg bg-secondary/50 p-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-teal-500/10 text-xs font-bold text-teal-500">
                  {i + 1}
                </span>
                <p className="text-sm">{tip}</p>
              </motion.div>
            ))}
            {!workoutSuggestions.length && <EmptyState text="No information available. Complete your profile to receive workout guidance." />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-muted/20 p-4 text-center text-sm text-muted-foreground">
      {text}
    </div>
  )
}
