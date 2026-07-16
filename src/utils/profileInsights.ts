import type { ConversationSummary, FullProfile, Memory, Report } from '@/types'

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

export function calculateDomainScores(profile?: FullProfile) {
  const career = clamp(
    40 +
      (profile?.career?.current_skills?.length ? 12 : 0) +
      (profile?.career?.target_role ? 12 : 0) +
      (profile?.career?.education ? 10 : 0) +
      (profile?.career?.career_goal ? 8 : 0) +
      (profile?.career?.experience_level ? 8 : 0),
    0,
    100,
  )

  const health = clamp(
    45 +
      (profile?.health?.fitness_goal ? 12 : 0) +
      (profile?.health?.sleep_hours ? 8 : 0) +
      (profile?.health?.water_intake ? 8 : 0) +
      (profile?.health?.workout ? 10 : 0) +
      (profile?.health?.diet_preference ? 7 : 0),
    0,
    100,
  )

  const finance = clamp(
    42 +
      (profile?.finance?.monthly_income ? 12 : 0) +
      (profile?.finance?.monthly_expenses ? 10 : 0) +
      (profile?.finance?.savings_goal ? 10 : 0) +
      (profile?.finance?.risk_appetite ? 8 : 0) +
      (profile?.finance?.investment_experience ? 8 : 0),
    0,
    100,
  )

  return {
    career,
    health,
    finance,
    overall: Math.round((career + health + finance) / 3),
  }
}

export function buildCareerPageData(profile?: FullProfile) {
  const skills = (profile?.career?.current_skills ?? []).length
    ? (profile?.career?.current_skills ?? []).slice(0, 6).map((skill, index) => ({
        name: skill,
        level: clamp(70 + index * 4, 65, 95),
        category: index % 2 === 0 ? 'Technical' : 'Soft',
      }))
    : [
        { name: 'Career foundation', level: 68, category: 'Planning' },
        { name: 'Communication', level: 72, category: 'Soft' },
      ]

  const targetRole = profile?.career?.target_role || 'your target role'
  const roadmap = [
    {
      phase: 'Foundation',
      duration: '2-4 weeks',
      tasks: [`Define goals around ${targetRole}`, 'Map current strengths to gaps', 'Create a short action plan'],
    },
    {
      phase: 'Growth',
      duration: '4-8 weeks',
      tasks: ['Build visible portfolio work', 'Practice core interview and communication skills', 'Track outcomes weekly'],
    },
    {
      phase: 'Advance',
      duration: '8-12 weeks',
      tasks: ['Engage with relevant communities', 'Seek feedback and mentorship', 'Prepare for applications and interviews'],
    },
  ]

  const currentSalary = profile?.finance?.monthly_income ? profile.finance.monthly_income * 12 : 0
  const predictedSalary = currentSalary ? Math.round(currentSalary * 1.25) : 0

  const certifications = profile?.career?.target_role
    ? [
        `Role-focused learning for ${profile.career.target_role}`,
        'Portfolio project validation',
        'Communication and leadership practice',
      ]
    : ['Portfolio project validation', 'Communication and leadership practice']

  const jobRecommendations = profile?.career?.target_role
    ? [{ title: profile.career.target_role, company: 'Aligned opportunities', match: 82 }]
    : []

  const progressData = [
    { month: 'Jan', skills: Math.max(30, skills.length * 8), projects: 1 },
    { month: 'Feb', skills: Math.max(38, skills.length * 10), projects: 2 },
    { month: 'Mar', skills: Math.max(45, skills.length * 12), projects: 2 },
    { month: 'Apr', skills: Math.max(52, skills.length * 13), projects: 3 },
    { month: 'May', skills: Math.max(60, skills.length * 14), projects: 3 },
    { month: 'Jun', skills: Math.max(68, skills.length * 15), projects: 4 },
  ]

  return {
    skills,
    roadmap,
    salaryPrediction: { current: currentSalary, predicted: predictedSalary, timeframe: '6 months' },
    certifications,
    jobRecommendations,
    progressData,
  }
}

export function buildHealthPageData(profile?: FullProfile) {
  const heightM = profile?.general?.height_cm ? profile.general.height_cm / 100 : 0
  const weightKg = profile?.general?.weight_kg || 0
  const bmi = heightM && weightKg ? Number(((weightKg / (heightM * heightM)) || 0).toFixed(1)) : 0
  const bmiStatus = bmi > 0 ? (bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese') : 'Pending'
  const sleepHours = profile?.health?.sleep_hours || 7.5
  const sleepQuality = profile?.health?.sleep_quality || 7
  const stressLevel = profile?.health?.medical_conditions ? 4 : 5
  const targetCalories = weightKg ? Math.round(weightKg * 15 + 500) : 2200
  const waterTarget = profile?.health?.water_intake ? Math.round(profile.health.water_intake) : 8

  const weeklyActivity = [
    { day: 'Mon', steps: 7800, workout: 30 },
    { day: 'Tue', steps: 6500, workout: 0 },
    { day: 'Wed', steps: 8400, workout: 45 },
    { day: 'Thu', steps: 7600, workout: 20 },
    { day: 'Fri', steps: 9000, workout: 35 },
    { day: 'Sat', steps: 7200, workout: 60 },
    { day: 'Sun', steps: 6800, workout: 0 },
  ]

  const dietSuggestions = profile?.health?.diet_preference
    ? [`Keep ${profile.health.diet_preference.toLowerCase()} meals balanced`, 'Add protein-rich options to support recovery', 'Hydrate consistently across the day']
    : ['Keep meals balanced and consistent', 'Add protein-rich options to support recovery', 'Hydrate consistently across the day']

  const workoutSuggestions = profile?.health?.fitness_goal
    ? [`Work towards ${profile.health.fitness_goal}`, 'Add mobility work after workouts', 'Track consistency for 4 weeks']
    : ['Maintain a steady weekly routine', 'Add mobility work after workouts', 'Track consistency for 4 weeks']

  return {
    bmi,
    bmiStatus,
    sleep: { hours: Number(sleepHours.toFixed(1)), quality: sleepQuality, trend: sleepQuality >= 7 ? 'steady' : 'improving' },
    stress: { level: stressLevel, trend: stressLevel <= 4 ? 'stable' : 'watch' },
    calories: { consumed: 1850, target: targetCalories, burned: 420 },
    water: { glasses: Math.min(8, waterTarget), target: waterTarget },
    weeklyActivity,
    dietSuggestions,
    workoutSuggestions,
  }
}

export function buildFinancePageData(profile?: FullProfile) {
  const monthlyIncome = profile?.finance?.monthly_income || 0
  const monthlyExpenses = profile?.finance?.monthly_expenses || 0
  const savings = Math.max(0, monthlyIncome - monthlyExpenses)
  const savingsRate = monthlyIncome > 0 ? (savings / monthlyIncome) * 100 : 0

  const budgetBreakdown = [
    { name: 'Housing', value: Math.max(0, monthlyExpenses * 0.3), color: '#10b981' },
    { name: 'Food', value: Math.max(0, monthlyExpenses * 0.18), color: '#14b8a6' },
    { name: 'Transport', value: Math.max(0, monthlyExpenses * 0.12), color: '#06b6d4' },
    { name: 'Utilities', value: Math.max(0, monthlyExpenses * 0.1), color: '#8b5cf6' },
    { name: 'Entertainment', value: Math.max(0, monthlyExpenses * 0.08), color: '#f59e0b' },
    { name: 'Savings', value: Math.max(0, savings), color: '#22c55e' },
    { name: 'Other', value: Math.max(0, monthlyExpenses - (monthlyExpenses * 0.3 + monthlyExpenses * 0.18 + monthlyExpenses * 0.12 + monthlyExpenses * 0.1 + monthlyExpenses * 0.08 + savings)), color: '#64748b' },
  ]

  const monthlyTrend = [
    { month: 'Jan', income: Math.max(0, monthlyIncome - 5000), expenses: Math.max(0, monthlyExpenses - 2000), savings: Math.max(0, savings - 1000) },
    { month: 'Feb', income: monthlyIncome, expenses: monthlyExpenses, savings },
    { month: 'Mar', income: Math.max(0, monthlyIncome + 3000), expenses: Math.max(0, monthlyExpenses + 1000), savings: Math.max(0, savings + 1500) },
    { month: 'Apr', income: Math.max(0, monthlyIncome + 2500), expenses: Math.max(0, monthlyExpenses + 800), savings: Math.max(0, savings + 1200) },
    { month: 'May', income: Math.max(0, monthlyIncome + 1500), expenses: Math.max(0, monthlyExpenses + 1000), savings: Math.max(0, savings + 1000) },
    { month: 'Jun', income: monthlyIncome, expenses: monthlyExpenses, savings },
  ]

  const riskProfile = profile?.finance?.risk_appetite || 'Balanced'
  const portfolio = [
    { asset: 'Core holdings', allocation: 50, value: Math.max(0, savings * 2) },
    { asset: 'Emergency fund', allocation: 25, value: Math.max(0, savings * 1.2) },
    { asset: 'Growth options', allocation: 15, value: Math.max(0, savings * 0.8) },
    { asset: 'Cash buffer', allocation: 10, value: Math.max(0, savings * 0.4) },
  ]
  const investments = profile?.finance?.investments
    ? profile.finance.investments.split(',').map((item) => item.trim()).filter(Boolean)
    : ['Maintain emergency reserves', 'Review automatic transfers monthly', 'Increase retirement contributions gradually']

  return {
    monthlyIncome,
    monthlyExpenses,
    savings,
    savingsRate,
    budgetBreakdown,
    monthlyTrend,
    riskProfile,
    portfolio,
    investments,
  }
}

export function buildDashboardActivity(
  profile?: FullProfile,
  conversations?: ConversationSummary[] | null,
  memories?: Memory[] | null,
  reports?: Report[] | null,
) {
  const activities: Array<{
    id: string
    type: 'chat' | 'memory' | 'report' | 'profile'
    title: string
    domain: string
    timestamp: string
  }> = [
    ...(conversations?.slice(0, 2).map((conversation) => ({
      id: conversation.id,
      type: 'chat' as const,
      title: `Conversation in ${conversation.domain} domain`,
      domain: conversation.domain,
      timestamp: conversation.created_at,
    })) || []),
    ...(memories?.slice(0, 2).map((memory) => ({
      id: memory.id,
      type: 'memory' as const,
      title: memory.memory_text,
      domain: memory.category,
      timestamp: memory.created_at,
    })) || []),
    ...(reports?.slice(0, 1).map((report) => ({
      id: report.id,
      type: 'report' as const,
      title: report.report_name,
      domain: 'auto',
      timestamp: report.generated_at,
    })) || []),
  ]

  if (profile) {
    activities.unshift({
      id: 'profile-update',
      type: 'profile' as const,
      title: 'Profile updated with latest preferences',
      domain: 'auto',
      timestamp: profile.general?.updated_at || profile.career?.updated_at || profile.health?.updated_at || profile.finance?.updated_at || new Date().toISOString(),
    })
  }

  return activities.slice(0, 5)
}

export function buildDashboardInsights(profile?: FullProfile) {
  const career = profile?.career?.target_role || 'career goals'
  const health = profile?.health?.fitness_goal || 'wellness goals'
  const finance = profile?.finance?.financial_goals || 'financial goals'

  return {
    career: profile?.career?.current_skills?.length
      ? `Your ${profile.career.current_skills.slice(0, 2).join(' and ')} focus is shaping your next move.`
      : `Add skills for ${career} to strengthen your profile.`,
    health: profile?.health?.sleep_hours
      ? `Sleep and recovery are being used to guide your ${health.toLowerCase()} plan.`
      : `Set health goals to tailor better ${health.toLowerCase()} recommendations.`,
    finance: profile?.finance?.monthly_income
      ? `Income and expenses are informing your ${finance.toLowerCase()} plan.`
      : `Add income and expense details to refine your ${finance.toLowerCase()} guidance.`,
  }
}

export function buildDashboardTrendValues(profile?: FullProfile) {
  const dataPoints = [
    profile?.career?.current_skills?.length ? 1 : 0,
    profile?.health?.fitness_goal ? 1 : 0,
    profile?.finance?.monthly_income ? 1 : 0,
    profile?.general?.location ? 1 : 0,
  ].reduce((sum, value) => sum + value, 0)

  const completion = (dataPoints / 4) * 100

  return {
    overall: Math.round(completion),
    conversations: profile?.general?.age ? 5 : 2,
    memories: profile?.career?.target_role ? 4 : 2,
    reports: profile?.finance?.savings_goal ? 3 : 1,
  }
}
