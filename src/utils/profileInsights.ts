import type { ConversationSummary, FullProfile, Memory, Report } from '@/types'
export function calculateDomainScores(profile?: FullProfile) {
  const careerFields = [
    profile?.career?.current_skills?.length,
    profile?.career?.target_role,
    profile?.career?.education,
    profile?.career?.career_goal,
    profile?.career?.experience_level,
  ]
  const healthFields = [
    profile?.health?.fitness_goal,
    profile?.health?.sleep_hours,
    profile?.health?.water_intake,
    profile?.health?.workout,
    profile?.health?.diet_preference,
  ]
  const financeFields = [
    profile?.finance?.monthly_income,
    profile?.finance?.monthly_expenses,
    profile?.finance?.savings_goal,
    profile?.finance?.risk_appetite,
    profile?.finance?.investment_experience,
  ]
  const scoreFromFields = (fields: Array<string | number | undefined>) => {
    const completedFields = fields.filter((field) => field !== undefined && field !== '').length
    return completedFields >= 2 ? Math.round((completedFields / fields.length) * 100) : null
  }
  const career = scoreFromFields(careerFields)
  const health = scoreFromFields(healthFields)
  const finance = scoreFromFields(financeFields)
  const overall = career !== null && health !== null && finance !== null
    ? Math.round((career + health + finance) / 3)
    : null
  return {
    career,
    health,
    finance,
    overall,
  }
}
export function buildCareerPageData(profile?: FullProfile) {
  const skills = profile?.career?.current_skills ?? []
  const currentSalary = profile?.finance?.monthly_income
    ? profile.finance.monthly_income * 12
    : null
  return {
    skills,
    currentSalary,
  }
}
export function buildHealthPageData(profile?: FullProfile) {
  const heightCm = profile?.general?.height_cm
  const weightKg = profile?.general?.weight_kg
  const bmi = heightCm != null && weightKg != null
    ? Number((weightKg / ((heightCm / 100) ** 2)).toFixed(1))
    : null
  const bmiStatus = bmi == null ? 'Not provided' : bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese'
  const sleepHours = profile?.health?.sleep_hours ?? null
  const sleepQuality = profile?.health?.sleep_quality ?? null
  const stressLevel = null
  const dietSuggestions = profile?.health?.diet_preference
    ? [`Keep ${profile.health.diet_preference.toLowerCase()} meals balanced`]
    : []
  const workoutSuggestions = profile?.health?.fitness_goal
    ? [`Work towards ${profile.health.fitness_goal}`]
    : []
  return {
    bmi,
    bmiStatus,
    sleep: { hours: sleepHours, quality: sleepQuality },
    stress: { level: stressLevel },
    waterIntake: profile?.health?.water_intake ?? null,
    dietSuggestions,
    workoutSuggestions,
  }
}
export function buildFinancePageData(profile?: FullProfile) {
  const monthlyIncome = profile?.finance?.monthly_income || 0
  const monthlyExpenses = profile?.finance?.monthly_expenses || 0
  const savings = monthlyIncome - monthlyExpenses
  const savingsRate = monthlyIncome > 0 ? (savings / monthlyIncome) * 100 : 0
  const budgetBreakdown: Array<{ name: string; value: number; color: string }> = []
  const monthlyTrend: Array<{ month: string; income: number; expenses: number; savings: number }> = []
  const riskProfile = profile?.finance?.risk_appetite ?? null
  const portfolio: Array<{ asset: string; allocation: number; value: number }> = []
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
  if (profile) {
    const profileUpdatedAt =
      profile.general?.updated_at || profile.career?.updated_at || profile.health?.updated_at || profile.finance?.updated_at
    if (profileUpdatedAt) {
      activities.unshift({
        id: 'profile-update',
        type: 'profile' as const,
        title: 'Profile updated with latest preferences',
        domain: 'auto',
        timestamp: profileUpdatedAt,
      })
    }
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
