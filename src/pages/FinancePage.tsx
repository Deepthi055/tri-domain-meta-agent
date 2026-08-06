import { motion } from 'framer-motion'
import {
  ArrowDownRight,
  ArrowUpRight,
  PiggyBank,
  Shield,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
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
import { formatCurrency, formatPercent } from '@/utils'
import { buildFinancePageData } from '@/utils/profileInsights'

export function FinancePage() {
  const { data: profile } = useProfile()
  const financeData = useMemo(() => buildFinancePageData(profile), [profile])
  const {
    monthlyIncome,
    monthlyExpenses,
    savings,
    savingsRate,
    budgetBreakdown,
    monthlyTrend,
    riskProfile,
    portfolio,
    investments,
  } = financeData

  return (
    <div className="space-y-8">
      <PageHeader
        title="Finance Dashboard"
        description="Budget tracking, savings, and investment guidance"
        badge="Finance"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Finance Score"
          value={Math.max(55, Math.round(savingsRate + 50))}
          subtitle="Financial health"
          icon={TrendingUp}
          trend={{ value: 4.1, label: 'this quarter' }}
          gradient="from-amber-500 to-orange-500"
        />
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

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Budget Breakdown" description="Monthly expense distribution">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={budgetBreakdown}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
              >
                {budgetBreakdown.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {budgetBreakdown.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-muted-foreground">{item.name}</span>
                <span className="ml-auto font-medium">{formatCurrency(item.value)}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Monthly Trend" description="Income, expenses, and savings over time">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={monthlyTrend}>
              <defs>
                <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="month" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
              <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Area type="monotone" dataKey="income" stroke="#10b981" fill="url(#incomeGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="expenses" stroke="#f43f5e" fill="url(#expenseGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
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
            <div className="flex items-center justify-center mb-4">
              <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20 text-sm px-4 py-1">
                {riskProfile}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground text-center">
              Balanced approach with moderate equity exposure and stable debt instruments.
            </p>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Wallet className="h-4 w-4 text-primary" />
              Portfolio Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {portfolio.map((asset) => (
              <div key={asset.asset}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{asset.asset}</span>
                  <span className="text-sm text-muted-foreground">
                    {formatCurrency(asset.value)} ({asset.allocation}%)
                  </span>
                </div>
                <Progress value={asset.allocation} className="h-1.5" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Investment Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>
    </div>
  )
}
