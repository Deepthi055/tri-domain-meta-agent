import { motion } from 'framer-motion'
import {
  ArrowDownRight,
  ArrowUpRight,
  PiggyBank,
  Shield,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProfile } from '@/hooks'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/utils/constants'
import { formatCurrency, formatPercent } from '@/utils'
import { buildFinancePageData } from '@/utils/profileInsights'

export function FinancePage() {
  const { data: profile, isLoading: isProfileLoading } = useProfile()
  const navigate = useNavigate()
  const financeData = useMemo(() => buildFinancePageData(profile), [profile])
  const {
    monthlyIncome,
    monthlyExpenses,
    savings,
    savingsRate,
    riskProfile,
    investments,
  } = financeData

  if (isProfileLoading) {
    return (
      <div className="space-y-8">
        <PageHeader title="Finance Dashboard" description="Loading profile..." />
        <div className="flex justify-center py-12"><div className="loader" /></div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="space-y-8">
        <PageHeader title="Finance Dashboard" description="Complete your profile to see financial insights" badge="Profile Needed" />
        <Card>
          <CardContent className="p-8 text-center">
            <h3 className="text-lg font-semibold mb-2">No finance profile yet</h3>
            <p className="text-sm text-muted-foreground mb-4">Add your income and expenses in the profile to view personalized budgets and recommendations.</p>
            <Button variant="gradient" onClick={() => navigate(ROUTES.PROFILE)}>Edit Profile</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Finance Dashboard"
        description="Budget tracking, savings, and investment guidance"
        badge="Finance"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Monthly Income"
          value={formatCurrency(monthlyIncome)}
          subtitle="Gross earnings"
          icon={ArrowUpRight}
          gradient="from-emerald-500 to-teal-500"
        />
        <MetricCard
          title="Monthly Expenses"
          value={formatCurrency(monthlyExpenses)}
          subtitle="Total spending"
          icon={ArrowDownRight}
          gradient="from-rose-500 to-pink-500"
        />
        <MetricCard
          title="Savings"
          value={formatCurrency(savings)}
          subtitle={formatPercent(savingsRate, 1) + ' savings rate'}
          icon={PiggyBank}
          gradient="from-blue-500 to-indigo-500"
        />
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Budget Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Budget allocation data not available yet.</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="h-4 w-4 text-primary" />
              Risk Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            {riskProfile ? (
              <div className="flex items-center justify-center mb-4">
                <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20 text-sm px-4 py-1">
                  {riskProfile}
                </Badge>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center">No risk profile saved yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Wallet className="h-4 w-4 text-primary" />
              Portfolio Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Portfolio data not available yet.</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Investment Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          {investments.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {investments.map((rec, i) => (
                <motion.div
                  key={rec}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-3 rounded-xl border p-4 hover:shadow-card-hover transition-shadow"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
                    <TrendingUp className="h-4 w-4 text-emerald-500" />
                  </div>
                  <p className="text-sm">{rec}</p>
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No investment recommendations yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
