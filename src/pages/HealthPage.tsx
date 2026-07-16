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
import { useProfile } from '@/hooks'
import { buildHealthPageData } from '@/utils/profileInsights'

export function HealthPage() {
  const { data: profile } = useProfile()
  const healthData = useMemo(() => buildHealthPageData(profile), [profile])
  const { bmi, bmiStatus, sleep, stress, calories, water, weeklyActivity, dietSuggestions, workoutSuggestions } = healthData

  const bmiColor = bmi < 25 ? 'text-emerald-500' : 'text-amber-500'

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
          value={Math.max(60, Math.round((profile?.health?.sleep_hours || 0) * 8 + (profile?.health?.sleep_quality || 0) * 3 + 40))}
          subtitle="Overall wellness"
          icon={Heart}
          trend={{ value: 3.5, label: 'this month' }}
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
          value={`${sleep.hours}h`}
          subtitle={`Quality: ${sleep.quality}/10`}
          icon={Moon}
          gradient="from-indigo-500 to-purple-500"
        />
        <MetricCard
          title="Stress Level"
          value={`${stress.level}/10`}
          subtitle={stress.trend}
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
                <defs>
                  <linearGradient id="bmiGrad">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="100%" stopColor="#14b8a6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold">{bmi}</span>
                <span className={`text-xs font-medium ${bmiColor}`}>{bmiStatus}</span>
              </div>
            </div>
            <p className="text-sm text-muted-foreground text-center mt-4">
              Healthy BMI range: 18.5 – 24.9
            </p>
          </CardContent>
        </Card>

        <ChartCard title="Weekly Activity" description="Steps and workout minutes" className="lg:col-span-2">
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
                <p className="text-xl font-bold">{calories.consumed} / {calories.target}</p>
              </div>
            </div>
            <Progress value={(calories.consumed / calories.target) * 100} className="h-2 mb-2" />
            <p className="text-xs text-muted-foreground">Burned: {calories.burned} kcal today</p>
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
                <p className="text-xl font-bold">{water.glasses} / {water.target} glasses</p>
              </div>
            </div>
            <Progress value={(water.glasses / water.target) * 100} className="h-2" />
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
                <p className="text-xl font-bold">{sleep.quality}/10</p>
              </div>
            </div>
            <Badge variant="secondary" className="text-[10px] capitalize">{sleep.trend}</Badge>
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
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
