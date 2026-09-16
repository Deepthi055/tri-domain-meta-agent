
import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Moon,
  Scale,
  Utensils,
  Dumbbell,
} from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useHealthAssessment, useProfile } from '@/hooks'
import { getErrorMessage } from '@/services'
import { Button } from '@/components/ui/button'
import { ROUTES, STORAGE_KEYS } from '@/utils/constants'
import type { MedicalReportResponse } from '@/types'
import { buildHealthPageData } from '@/utils/profileInsights'

export function HealthPage() {
  const { user } = useAuth()
  const { data: profile, isLoading: isProfileLoading } = useProfile()
  const healthAssessment = useHealthAssessment()
  const [fitnessInputMessage, setFitnessInputMessage] = useState<string | null>(null)
  const [medicalReport, setMedicalReport] = useState<MedicalReportResponse | null>(null)
  const navigate = useNavigate()
  const healthData = useMemo(() => buildHealthPageData(profile), [profile])
  const { bmi, bmiStatus, sleep, stress, waterIntake, dietSuggestions, workoutSuggestions } = healthData

  useEffect(() => {
    if (!user?.id) return
    const storedReport = localStorage.getItem(`${STORAGE_KEYS.MEDICAL_REPORT_RESULT}:${user.id}`)
    if (!storedReport) return
    try {
      setMedicalReport(JSON.parse(storedReport) as MedicalReportResponse)
    } catch {
      localStorage.removeItem(`${STORAGE_KEYS.MEDICAL_REPORT_RESULT}:${user.id}`)
    }
  }, [user?.id])

  const bmiColor = bmi != null && bmi < 25 ? 'text-emerald-500' : 'text-amber-500'
  const handleFitnessScoreCheck = () => {
    if (!profile) {
      setFitnessInputMessage('Complete your health profile before calculating your Fitness Score.')
      return
    }

    const inputs = {
      sleep_quality: profile.health?.sleep_quality,
      stress_level: profile.health?.stress_level,
      mood_score: profile.health?.mood_score,
      active_days_per_week: profile.health?.active_days_per_week,
    }
    if (Object.values(inputs).some((value) => value == null)) {
      setFitnessInputMessage('Complete sleep quality, stress level, mood score, and active days per week in your profile first.')
      return
    }
    setFitnessInputMessage(null)
    healthAssessment.mutate(inputs as {
      sleep_quality: number
      stress_level: number
      mood_score: number
      active_days_per_week: number
    })
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

      {medicalReport ? (
        <Card className="overflow-hidden border-emerald-500/20 shadow-lg shadow-emerald-500/5">
          <div className="bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-cyan-500/15 px-6 py-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500 text-white shadow-md shadow-emerald-500/25">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">Latest report</p>
                  <h2 className="text-lg font-semibold">{medicalReport.filename}</h2>
                </div>
              </div>
              <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Explained in plain language
              </span>
            </div>
          </div>
          <CardContent className="space-y-5 p-6">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Summary</p>
              <p className="text-base leading-7">{medicalReport.analysis.summary}</p>
            </div>
            {medicalReport.analysis.findings.length > 0 ? (
              <div>
                <p className="mb-3 text-sm font-semibold">What the report says</p>
                <div className="grid gap-3 md:grid-cols-2">
                  {medicalReport.analysis.findings.map((finding) => (
                    <div key={`${finding.item}-${finding.meaning}`} className="rounded-xl border bg-muted/20 p-4">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className={`mt-0.5 h-4 w-4 shrink-0 ${finding.severity === 'urgent' ? 'text-red-500' : finding.severity === 'watch' ? 'text-amber-500' : 'text-emerald-500'}`} />
                        <div>
                          <p className="text-sm font-semibold">{finding.item}</p>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">{finding.meaning}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-xl bg-teal-500/10 p-4">
                <p className="mb-2 text-sm font-semibold text-teal-800 dark:text-teal-200">Next steps</p>
                <ul className="list-disc space-y-1.5 pl-5 text-sm leading-6 text-muted-foreground">
                  {medicalReport.analysis.next_steps.map((step) => <li key={step}>{step}</li>)}
                </ul>
              </div>
              <div className="rounded-xl bg-emerald-500/10 p-4">
                <p className="mb-2 text-sm font-semibold text-emerald-800 dark:text-emerald-200">A note for you</p>
                <p className="text-sm leading-6 text-muted-foreground">{medicalReport.analysis.reassurance}</p>
              </div>
            </div>
            <p className="border-t pt-4 text-xs leading-5 text-muted-foreground">{medicalReport.analysis.disclaimer}</p>
          </CardContent>
        </Card>
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
