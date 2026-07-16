import { useEffect, useState } from 'react'
import { Bell, Globe, Key, Moon, Palette, Shield, Sun } from 'lucide-react'
import { toast } from 'sonner'
import { useTheme } from '@/contexts/ThemeContext'
import { useLanguage } from '@/contexts/LanguageContext'
import { useApiStatus } from '@/hooks'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

export function SettingsPage() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const { language, setLanguage, t } = useLanguage()
  const { data: apiStatus } = useApiStatus()
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    reports: true,
    insights: true,
  })
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')

  useEffect(() => {
    const stored = localStorage.getItem('tridomain_notifications')
    if (stored) {
      try {
        setNotifications(JSON.parse(stored))
      } catch {
        setNotifications({ email: true, push: false, reports: true, insights: true })
      }
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('tridomain_notifications', JSON.stringify(notifications))
  }, [notifications])

  const handleSaveApi = () => {
    toast.success('API settings saved (requires restart)')
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <PageHeader title="Settings" description="Customize your TriDomain experience" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Palette className="h-4 w-4" /> Appearance
          </CardTitle>
          <CardDescription>Customize the look and feel</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {resolvedTheme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              <div>
                <Label>Theme</Label>
                <p className="text-xs text-muted-foreground">Select your preferred theme</p>
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
            <Bell className="h-4 w-4" /> Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: 'email' as const, label: 'Email notifications', desc: 'Receive updates via email' },
            { key: 'push' as const, label: 'Push notifications', desc: 'Browser push alerts' },
            { key: 'reports' as const, label: 'Report ready alerts', desc: 'When reports are generated' },
            { key: 'insights' as const, label: 'AI insights', desc: 'Weekly domain insights' },
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
            <Globe className="h-4 w-4" /> Language
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="hi">Hindi</SelectItem>
              <SelectItem value="es">Spanish</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Shield className="h-4 w-4" /> Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Two-factor authentication</Label>
              <p className="text-xs text-muted-foreground">Add an extra layer of security</p>
            </div>
            <Button variant="outline" size="sm">Enable</Button>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label>Change password</Label>
              <p className="text-xs text-muted-foreground">Update your account password</p>
            </div>
            <Button variant="outline" size="sm">Update</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Key className="h-4 w-4" /> API Settings
          </CardTitle>
          <CardDescription>Backend connection configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>API Base URL</Label>
            <Input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} placeholder="http://127.0.0.1:8000" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>API Status</Label>
              <p className="text-xs text-muted-foreground">
                {apiStatus?.system || 'TriDomain Meta-Agent API'}
              </p>
            </div>
            <Badge variant={apiStatus?.status === 'ok' ? 'secondary' : 'outline'}>
              {apiStatus?.status || 'checking...'}
            </Badge>
          </div>
          <Button variant="gradient" onClick={handleSaveApi}>Save API Settings</Button>
        </CardContent>
      </Card>
    </div>
  )
}
