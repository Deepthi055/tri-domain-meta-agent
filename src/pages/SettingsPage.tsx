import { useEffect, useState } from 'react'
import { Bell, Globe, Moon, Palette, Shield, Sun } from 'lucide-react'
import { toast } from 'sonner'
import { useTheme } from '@/contexts/ThemeContext'
import { useLanguage } from '@/contexts/LanguageContext'
import { useAuth } from '@/contexts/AuthContext'
import { authService, getErrorMessage } from '@/services'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { STORAGE_KEYS } from '@/utils/constants'

export function SettingsPage() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const { user, setUser } = useAuth()
  const { language, setLanguage, t } = useLanguage()
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    reports: true,
    insights: true,
  })
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false)
  const [changePasswordLoading, setChangePasswordLoading] = useState(false)
  const [twoFactorLoading, setTwoFactorLoading] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS)
    if (stored) {
      try {
        setNotifications(JSON.parse(stored))
      } catch {
        setNotifications({ email: true, push: false, reports: true, insights: true })
      }
    }
  }, [])

  useEffect(() => {
    setTwoFactorEnabled(user?.two_factor_enabled ?? false)
  }, [user])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS, JSON.stringify(notifications))
  }, [notifications])

  const handleSaveSettings = () => {
    toast.success(t('profileSaved'))
  }

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }
    setChangePasswordLoading(true)
    try {
      await authService.changePassword(currentPassword, newPassword)
      toast.success('Password changed successfully')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setChangePasswordLoading(false)
    }
  }

  const handleTwoFactorToggle = async () => {
    setTwoFactorLoading(true)
    try {
      const updatedUser = await authService.setTwoFactorEnabled(twoFactorEnabled, currentPassword)
      authService.saveUser(updatedUser)
      setUser(updatedUser)
      toast.success(`Two-factor authentication ${twoFactorEnabled ? 'enabled' : 'disabled'}`)
    } catch (err) {
      toast.error(getErrorMessage(err))
      setTwoFactorEnabled(!twoFactorEnabled)
    } finally {
      setTwoFactorLoading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <PageHeader title={t('settings')} description={t('notificationsSettings')} />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Palette className="h-4 w-4" /> {t('appearance')}
          </CardTitle>
          <CardDescription>{t('theme')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {resolvedTheme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              <div>
                <Label>{t('theme')}</Label>
                <p className="text-xs text-muted-foreground">{t('selectLanguage')}</p>
              </div>
            </div>
            <Select value={theme} onValueChange={(v) => setTheme(v as 'light' | 'dark' | 'system')}>
              <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Bell className="h-4 w-4" /> {t('notifications')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: 'email' as const, label: t('emailNotifications'), desc: 'Receive updates via email' },
            { key: 'push' as const, label: t('pushNotifications'), desc: 'Browser push alerts' },
            { key: 'reports' as const, label: t('reportNotifications'), desc: 'When reports are generated' },
            { key: 'insights' as const, label: t('aiInsights'), desc: 'Weekly domain insights' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between">
              <div>
                <Label>{item.label}</Label>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
              <Switch
                checked={notifications[item.key]}
                onCheckedChange={(c) => setNotifications((prev) => ({ ...prev, [item.key]: c }))}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Globe className="h-4 w-4" /> {t('language')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="hi">हिन्दी</SelectItem>
              <SelectItem value="kn">ಕನ್ನಡ</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Shield className="h-4 w-4" /> {t('security')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>{t('twoFactorAuthentication')}</Label>
            <p className="text-xs text-muted-foreground">Add an extra layer of security for your account</p>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <Switch checked={twoFactorEnabled} onCheckedChange={setTwoFactorEnabled} />
              <div className="flex flex-wrap gap-2">
                <Input
                  type="password"
                  placeholder="Current password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  className="min-w-[220px]"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTwoFactorToggle}
                  disabled={twoFactorLoading}
                >
                  {twoFactorLoading ? 'Saving...' : twoFactorEnabled ? 'Enable 2FA' : 'Disable 2FA'}
                </Button>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t('changePassword')}</Label>
            <p className="text-xs text-muted-foreground">Update your account password</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <Input
                type="password"
                placeholder="Current password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
              <Input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
              <Input
                type="password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
            </div>
            <Button variant="outline" size="sm" onClick={handleChangePassword} disabled={changePasswordLoading}>
              {changePasswordLoading ? 'Saving...' : 'Update Password'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button variant="gradient" onClick={handleSaveSettings}>{t('save')}</Button>
      </div>
    </div>
  )
}
