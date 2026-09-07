import { motion } from 'framer-motion'
import {
  Activity,
  Moon,
  Scale,
  Utensils,
  Dumbbell,
} from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHealthAssessment, useProfile } from '@/hooks'
import { getErrorMessage } from '@/services'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/utils/constants'
import { buildHealthPageData } from '@/utils/profileInsights'

export function HealthPage() {
  const { data: profile, isLoading: isProfileLoading } = useProfile()
  const healthAssessment = useHealthAssessment()
  const [fitnessInputMessage, setFitnessInputMessage] = useState<string | null>(null)
  const navigate = useNavigate()
  const healthData = useMemo(() => buildHealthPageData(profile), [profile])
  const { bmi, bmiStatus, sleep, stress, waterIntake, dietSuggestions, workoutSuggestions } = healthData

  const bmiColor = bmi != null && bmi < 25 ? 'text-emerald-500' : 'text-amber-500'
  const handleFitnessScoreCheck = () => {
    setFitnessInputMessage('Complete sleep quality, stress level, mood score, and active days per week to calculate your Fitness Score.')
  }

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
            <p className="text-sm text-muted-foreground mb-4">Provide basic health details to view saved health details, fitness score, and profile reminders.</p>
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
        description="Your saved health details, fitness score, and profile reminders"
        badge="Health"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="BMI"
          value={bmi ?? 'Add height and weight to calculate BMI.'}
          subtitle={bmiStatus}
          icon={Scale}
          gradient="from-blue-500 to-cyan-500"
        />
        <MetricCard
          title="Sleep"
          value={sleep.hours != null ? `${sleep.hours}h` : 'Not provided'}
          subtitle={sleep.quality != null ? `Quality: ${sleep.quality}/10` : 'Sleep quality not provided'}
          icon={Moon}
          gradient="from-indigo-500 to-purple-500"
        />
        <MetricCard
          title="Stress Level"
          value={stress.level != null ? `${stress.level}/10` : 'Not provided'}
          subtitle="Complete the fitness assessment to provide stress level"
          icon={Activity}
          gradient="from-rose-500 to-pink-500"
        />
        <Card>
          <CardContent className="flex h-full flex-col justify-between gap-3 p-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Fitness Score</p>
              {healthAssessment.data ? (
                <p className="text-3xl font-bold">{healthAssessment.data.value}</p>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">Complete the fitness assessment to see your Fitness Score.</p>
              )}
            </div>
            <Button
              variant="gradient"
              onClick={handleFitnessScoreCheck}
              disabled={healthAssessment.isPending}
            >
              {healthAssessment.isPending ? 'Checking...' : 'Check Fitness Score'}
            </Button>
            {fitnessInputMessage ? (
              <p className="text-xs text-muted-foreground">{fitnessInputMessage}</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {healthAssessment.isError ? (
        <p className="text-sm text-destructive">{getErrorMessage(healthAssessment.error)}</p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">BMI Analysis</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            {bmi != null ? (
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
            ) : (
              <p className="py-16 text-center text-sm text-muted-foreground">Add height and weight to calculate BMI.</p>
            )}
            <p className="text-sm text-muted-foreground text-center mt-4">
              Healthy BMI range: 18.5 – 24.9
            </p>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Weekly Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Activity data not available yet.</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Calories</p>
            <p className="mt-2 text-sm text-muted-foreground">Calorie data not available yet.</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Saved Water Intake</p>
            <p className="mt-2 text-xl font-bold">
              {waterIntake != null ? `${waterIntake} L/day` : 'Not provided'}
            </p>
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
                <p className="text-xl font-bold">{sleep.quality != null ? `${sleep.quality}/10` : 'Not provided'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Utensils className="h-4 w-4 text-primary" />
              Diet Profile Reminder
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dietSuggestions.length > 0 ? dietSuggestions.map((tip, i) => (
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
            )) : (
              <p className="text-sm text-muted-foreground">No diet preference saved yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Dumbbell className="h-4 w-4 text-primary" />
              Fitness Goal Reminder
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {workoutSuggestions.length > 0 ? workoutSuggestions.map((tip, i) => (
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
            )) : (
              <p className="text-sm text-muted-foreground">No fitness goal saved yet.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
