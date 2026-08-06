import type { ConversationSummary, FullProfile, Memory, Report } from '@/types'

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function hasValue(value: unknown) {
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'string') return value.trim().length > 0
  return value !== undefined && value !== null
}

export function hasProfileData(profile?: FullProfile) {
  return Boolean(
    profile &&
      [profile.general, profile.career, profile.health, profile.finance].some((section) =>
        section && Object.values(section).some(hasValue),
      ),
  )
}

export function calculateDomainScores(profile?: FullProfile) {
  const careerFields = [
    profile?.career?.education,
    profile?.career?.current_skills?.length,
    profile?.career?.target_role,
    profile?.career?.experience_level,
    profile?.career?.career_goal,
    profile?.career?.preferred_roles,
    profile?.career?.resume,
  ]
  const healthFields = [
    profile?.general?.height_cm,
    profile?.general?.weight_kg,
    profile?.health?.medical_conditions,
    profile?.health?.lifestyle,
    profile?.health?.fitness_goal,
    profile?.health?.sleep_hours,
    profile?.health?.sleep_quality,
    profile?.health?.diet_preference,
    profile?.health?.workout,
    profile?.health?.health_goals,
    profile?.health?.water_intake,
  ]
  const financeFields = [
    profile?.finance?.monthly_income,
    profile?.finance?.monthly_expenses,
    profile?.finance?.savings_goal,
    profile?.finance?.investments,
    profile?.finance?.risk_appetite,
    profile?.finance?.investment_experience,
    profile?.finance?.financial_goals,
    profile?.finance?.budget,
  ]

  const career = careerFields.filter(hasValue).length
  const health = healthFields.filter(hasValue).length
  const finance = financeFields.filter(hasValue).length

  const careerScore = career ? Math.round((career / careerFields.length) * 100) : 0
  const healthScore = health ? Math.round((health / healthFields.length) * 100) : 0
  const financeScore = finance ? Math.round((finance / financeFields.length) * 100) : 0

  return {
    career: careerScore,
    health: healthScore,
    finance: financeScore,
    overall: Math.round((careerScore + healthScore + financeScore) / 3),
  }
}

export function buildCareerPageData(profile?: FullProfile) {
  const skills = (profile?.career?.current_skills ?? []).slice(0, 6).map((skill, index) => ({
    name: skill,
    level: clamp(70 + index * 4, 65, 95),
    category: index % 2 === 0 ? 'Technical' : 'Soft',
  }))

  const targetRole = profile?.career?.target_role
  const roadmap = targetRole
    ? [
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
    : []

  const currentSalary = profile?.finance?.monthly_income ? profile.finance.monthly_income * 12 : null
  const predictedSalary = currentSalary ? Math.round(currentSalary * 1.25) : null

  const certifications = profile?.career?.target_role
    ? [
        `Role-focused learning for ${profile.career.target_role}`,
        'Portfolio project validation',
        'Communication and leadership practice',
      ]
    : []

  const jobRecommendations = profile?.career?.target_role ? [{ title: profile.career.target_role, company: 'Aligned opportunities', match: 82 }] : []

  const projectCount = profile?.career?.resume || profile?.career?.preferred_roles || profile?.career?.career_goal ? 1 : 0
  const progressData = profile?.career?.current_skills?.length
    ? [
        { month: 'Current', skills: skills.length * 10, projects: projectCount },
      ]
    : []

  return {
    skills,
    roadmap,
    salaryPrediction: { current: currentSalary, predicted: predictedSalary, timeframe: currentSalary ? 'based on current income' : 'No data available' },
    certifications,
    jobRecommendations,
    progressData,
  }
}

export function buildHealthPageData(profile?: FullProfile) {
  const heightM = profile?.general?.height_cm ? profile.general.height_cm / 100 : 0
  const weightKg = profile?.general?.weight_kg || 0
  const bmi = heightM && weightKg ? Number(((weightKg / (heightM * heightM)) || 0).toFixed(1)) : 0
  const bmiStatus = bmi > 0 ? (bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese') : 'No data available'
  const sleepHours = profile?.health?.sleep_hours ?? null
  const sleepQuality = profile?.health?.sleep_quality ?? null
  const stressLevel = profile?.health?.medical_conditions ? 4 : profile?.health?.fitness_goal ? 5 : null
  const targetCalories = weightKg ? Math.round(weightKg * 15 + 500) : null
  const waterTarget = profile?.health?.water_intake ? Math.round(profile.health.water_intake) : null

  const weeklyActivity = []

  const dietSuggestions = profile?.health?.diet_preference
    ? [`Keep ${profile.health.diet_preference.toLowerCase()} meals balanced`, 'Add protein-rich options to support recovery', 'Hydrate consistently across the day']
    : []

  const workoutSuggestions = profile?.health?.fitness_goal
    ? [`Work towards ${profile.health.fitness_goal}`, 'Add mobility work after workouts', 'Track consistency for 4 weeks']
    : []

  return {
    bmi,
    bmiStatus,
    sleep: { hours: sleepHours, quality: sleepQuality, trend: sleepQuality !== null && sleepQuality >= 7 ? 'steady' : 'improving' },
    stress: { level: stressLevel, trend: stressLevel !== null && stressLevel <= 4 ? 'stable' : 'watch' },
    calories: { consumed: null, target: targetCalories, burned: null },
    water: { glasses: null, target: waterTarget },
    weeklyActivity,
    dietSuggestions,
    workoutSuggestions,
  }
}

export function buildFinancePageData(profile?: FullProfile) {
  const monthlyIncome = profile?.finance?.monthly_income ?? null
  const monthlyExpenses = profile?.finance?.monthly_expenses ?? null
  const savings = monthlyIncome !== null && monthlyExpenses !== null ? Math.max(0, monthlyIncome - monthlyExpenses) : null
  const savingsRate = monthlyIncome && savings !== null ? (savings / monthlyIncome) * 100 : null

  const budgetBreakdown = monthlyExpenses !== null
    ? [
        { name: 'Housing', value: monthlyExpenses * 0.3, color: '#10b981' },
        { name: 'Food', value: monthlyExpenses * 0.18, color: '#14b8a6' },
        { name: 'Transport', value: monthlyExpenses * 0.12, color: '#06b6d4' },
        { name: 'Utilities', value: monthlyExpenses * 0.1, color: '#8b5cf6' },
        { name: 'Entertainment', value: monthlyExpenses * 0.08, color: '#f59e0b' },
        { name: 'Savings', value: savings ?? 0, color: '#22c55e' },
        { name: 'Other', value: Math.max(0, monthlyExpenses - (monthlyExpenses * 0.3 + monthlyExpenses * 0.18 + monthlyExpenses * 0.12 + monthlyExpenses * 0.1 + monthlyExpenses * 0.08 + (savings ?? 0))), color: '#64748b' },
      ]
    : []

  const monthlyTrend = monthlyIncome !== null && monthlyExpenses !== null && savings !== null
    ? [
        { month: 'Current', income: monthlyIncome, expenses: monthlyExpenses, savings },
      ]
    : []

  const riskProfile = profile?.finance?.risk_appetite ?? null
  const portfolio = monthlyIncome !== null && monthlyExpenses !== null && savings !== null
    ? [
        { asset: 'Core holdings', allocation: 50, value: Math.max(0, savings * 2) },
        { asset: 'Emergency fund', allocation: 25, value: Math.max(0, savings * 1.2) },
        { asset: 'Growth options', allocation: 15, value: Math.max(0, savings * 0.8) },
        { asset: 'Cash buffer', allocation: 10, value: Math.max(0, savings * 0.4) },
      ]
    : []
  const investments = profile?.finance?.investments
    ? profile.finance.investments.split(',').map((item) => item.trim()).filter(Boolean)
    : []

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

  if (profile && hasProfileData(profile)) {
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
  const career = profile?.career?.target_role
  const health = profile?.health?.fitness_goal
  const finance = profile?.finance?.financial_goals
  const healthGoal = health?.trim().toLowerCase()
  const financeGoal = finance?.trim().toLowerCase()

  return {
    career: profile?.career?.current_skills?.length
      ? `Your ${profile.career.current_skills.slice(0, 2).join(' and ')} focus is shaping your next move.`
      : 'Complete your profile to receive personalized recommendations.',
    health: profile?.health?.sleep_hours
      ? healthGoal
        ? `Sleep and recovery are being used to guide your ${healthGoal} plan.`
        : 'Sleep and recovery are being used to guide your health plan.'
      : 'Complete your profile to receive personalized recommendations.',
    finance: profile?.finance?.monthly_income
      ? financeGoal
        ? `Income and expenses are informing your ${financeGoal} plan.`
        : 'Income and expenses are informing your financial plan.'
      : 'Complete your profile to receive personalized recommendations.',
  }
}

export function buildDashboardTrendValues(profile?: FullProfile) {
  const fields = [
    profile?.general?.age,
    profile?.general?.gender,
    profile?.general?.height_cm,
    profile?.general?.weight_kg,
    profile?.general?.location,
    profile?.career?.education,
    profile?.career?.current_skills?.length,
    profile?.career?.target_role,
    profile?.career?.experience_level,
    profile?.career?.career_goal,
    profile?.health?.medical_conditions,
    profile?.health?.lifestyle,
    profile?.health?.fitness_goal,
    profile?.health?.sleep_hours,
    profile?.health?.sleep_quality,
    profile?.health?.diet_preference,
    profile?.health?.workout,
    profile?.health?.health_goals,
    profile?.health?.water_intake,
    profile?.finance?.monthly_income,
    profile?.finance?.monthly_expenses,
    profile?.finance?.savings_goal,
    profile?.finance?.investments,
    profile?.finance?.risk_appetite,
    profile?.finance?.investment_experience,
    profile?.finance?.financial_goals,
    profile?.finance?.budget,
  ]

  const completion = Math.round((fields.filter(hasValue).length / fields.length) * 100)
  const safeCompletion = Number.isFinite(completion) ? completion : 0

  return {
    overall: safeCompletion,
  }
}
