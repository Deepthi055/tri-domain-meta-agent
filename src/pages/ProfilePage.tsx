import { useEffect, useState, type ChangeEvent } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Save, User } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'
import { authService, getErrorMessage } from '@/services'
import { useProfile, useUpdateProfile, useCreateProfile } from '@/hooks'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { FullProfile } from '@/types'

const profileSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  general: z.object({
    age: z.coerce.number().min(1).max(120).optional(),
    gender: z.string().optional(),
    height_cm: z.coerce.number().min(50).max(300).optional(),
    weight_kg: z.coerce.number().min(20).max(500).optional(),
    location: z.string().optional(),
  }).optional(),
  career: z.object({
    current_skills: z.string().optional(),
    target_role: z.string().optional(),
    experience_level: z.string().optional(),
    career_goal: z.string().optional(),
  }).optional(),
  health: z.object({
    fitness_goal: z.string().optional(),
    sleep_hours: z.coerce.number().min(0).max(24).optional(),
    sleep_quality: z.coerce.number().min(1).max(10).optional(),
    diet_preference: z.string().optional(),
  }).optional(),
  finance: z.object({
    monthly_income: z.coerce.number().min(0).optional(),
    monthly_expenses: z.coerce.number().min(0).optional(),
    savings_goal: z.coerce.number().min(0).optional(),
    risk_appetite: z.string().optional(),
    investment_experience: z.string().optional(),
  }).optional(),
})

type ProfileForm = z.infer<typeof profileSchema>

export function ProfilePage() {
  const { user, setUser } = useAuth()
  const { t } = useLanguage()
  const { data: profile, isLoading } = useProfile()
  const updateProfile = useUpdateProfile()
  const createProfile = useCreateProfile()
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null)

  const { register, handleSubmit, reset } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
  })

  useEffect(() => {
    if (profile) {
      reset({
        name: user?.name || '',
        general: profile.general,
        career: {
          ...profile.career,
          current_skills: profile.career?.current_skills?.join(', '),
        },
        health: profile.health,
        finance: profile.finance,
      })
    } else {
      reset({
        name: user?.name || '',
      })
    }
  }, [profile, reset, user])

  const onSubmit = async (data: ProfileForm) => {
    const payload: FullProfile = {
      general: data.general,
      career: data.career
        ? {
            ...data.career,
            current_skills: data.career.current_skills
              ? data.career.current_skills.split(',').map((s) => s.trim()).filter(Boolean)
              : undefined,
          }
        : undefined,
      health: data.health,
      finance: data.finance,
    }

    try {
      if (data.name && data.name !== user?.name) {
        const updatedUser = await authService.updateCurrentUser(data.name)
        authService.saveUser(updatedUser)
        setUser(updatedUser)
      }
      if (profile && Object.keys(profile).length > 0) {
        await updateProfile.mutateAsync(payload)
      } else {
        await createProfile.mutateAsync(payload)
      }
      toast.success(t('profileSaved'))
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleAvatarUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadend = async () => {
      const url = reader.result as string
      try {
        const updatedUser = await authService.uploadAvatar(url)
        authService.saveUser(updatedUser)
        setUser(updatedUser)
        setAvatarUrl(updatedUser.avatar_url || null)
        toast.success(t('avatarUploaded'))
      } catch (err) {
        toast.error(getErrorMessage(err))
      }
    }
    reader.readAsDataURL(file)
  }

  const handleAvatarRemove = async () => {
    try {
      const updatedUser = await authService.uploadAvatar('')
      authService.saveUser(updatedUser)
      setUser(updatedUser)
      setAvatarUrl(null)
      toast.success(t('avatarDeleted'))
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const initials = user?.name?.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2) || 'U'
  const isSaving = updateProfile.isPending || createProfile.isPending

  if (isLoading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <PageHeader
        title="Profile"
        description="Manage your personal and domain-specific details"
        action={
          <Button variant="gradient" onClick={handleSubmit(onSubmit)} disabled={isSaving}>
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save Profile
          </Button>
        }
      />

      <Card>
        <CardContent className="flex items-center gap-6 p-6">
          <Avatar className="h-20 w-20">
            {user?.avatar_url ? (
              <AvatarImage src={user.avatar_url} alt="Avatar" />
            ) : (
              <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-500 text-white text-2xl">
                {initials}
              </AvatarFallback>
            )}
          </Avatar>
          <div>
            <h2 className="text-xl font-bold">{user?.name}</h2>
            <p className="text-muted-foreground">{user?.email}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <label htmlFor="avatarUpload" className="inline-flex cursor-pointer items-center rounded-full border border-input px-3 py-1 text-sm font-medium transition hover:bg-muted">
                {t('uploadAvatar')}
              </label>
              <input
                id="avatarUpload"
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={handleAvatarUpload}
              />
              {avatarUrl ? (
                <Button variant="outline" size="sm" onClick={handleAvatarRemove}>
                  {t('deleteAvatar')}
                </Button>
              ) : null}
            </div>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Tabs defaultValue="general">
          <TabsList className="mb-6">
            <TabsTrigger value="general">Personal</TabsTrigger>
            <TabsTrigger value="career">Career</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
            <TabsTrigger value="finance">Finance</TabsTrigger>
          </TabsList>

          <TabsContent value="general">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <User className="h-4 w-4" /> Personal Details
                </CardTitle>
                <CardDescription>Basic information used across all domains</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label>Name</Label>
                  <Input {...register('name')} placeholder="John Doe" />
                </div>
                <div className="space-y-2">
                  <Label>Age</Label>
                  <Input type="number" {...register('general.age')} placeholder="25" />
                </div>
                <div className="space-y-2">
                  <Label>Gender</Label>
                  <Input {...register('general.gender')} placeholder="Male / Female / Other" />
                </div>
                <div className="space-y-2">
                  <Label>Height (cm)</Label>
                  <Input type="number" {...register('general.height_cm')} placeholder="175" />
                </div>
                <div className="space-y-2">
                  <Label>Weight (kg)</Label>
                  <Input type="number" {...register('general.weight_kg')} placeholder="70" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Location</Label>
                  <Input {...register('general.location')} placeholder="Mumbai, India" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="career">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Career Details</CardTitle>
                <CardDescription>Skills and career goals for personalized advice</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label>Current Skills (comma-separated)</Label>
                  <Textarea {...register('career.current_skills')} placeholder="Python, SQL, Machine Learning" />
                </div>
                <div className="space-y-2">
                  <Label>Target Role</Label>
                  <Input {...register('career.target_role')} placeholder="Data Scientist" />
                </div>
                <div className="space-y-2">
                  <Label>Experience Level</Label>
                  <Select
                    value={watch('career.experience_level') || ''}
                    onValueChange={(v) => setValue('career.experience_level', v)}
                  >
                    <SelectTrigger><SelectValue placeholder="Select level" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="entry">Entry Level</SelectItem>
                      <SelectItem value="mid">Mid Level</SelectItem>
                      <SelectItem value="senior">Senior</SelectItem>
                      <SelectItem value="lead">Lead / Manager</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Career Goal</Label>
                  <Textarea {...register('career.career_goal')} placeholder="Transition to ML engineering..." />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="health">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Health Details</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Fitness Goal</Label>
                  <Input {...register('health.fitness_goal')} placeholder="Build muscle, lose weight..." />
                </div>
                <div className="space-y-2">
                  <Label>Sleep Hours</Label>
                  <Input type="number" step="0.5" {...register('health.sleep_hours')} placeholder="7.5" />
                </div>
                <div className="space-y-2">
                  <Label>Sleep Quality (1-10)</Label>
                  <Input type="number" {...register('health.sleep_quality')} placeholder="8" />
                </div>
                <div className="space-y-2">
                  <Label>Diet Preference</Label>
                  <Input {...register('health.diet_preference')} placeholder="Vegetarian, Keto..." />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="finance">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Financial Details</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Monthly Income (₹)</Label>
                  <Input type="number" {...register('finance.monthly_income')} placeholder="85000" />
                </div>
                <div className="space-y-2">
                  <Label>Monthly Expenses (₹)</Label>
                  <Input type="number" {...register('finance.monthly_expenses')} placeholder="52000" />
                </div>
                <div className="space-y-2">
                  <Label>Savings Goal (₹)</Label>
                  <Input type="number" {...register('finance.savings_goal')} placeholder="15000" />
                </div>
                <div className="space-y-2">
                  <Label>Risk Appetite</Label>
                  <Select
                    value={watch('finance.risk_appetite') || ''}
                    onValueChange={(v) => setValue('finance.risk_appetite', v)}
                  >
                    <SelectTrigger><SelectValue placeholder="Select risk level" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conservative">Conservative</SelectItem>
                      <SelectItem value="moderate">Moderate</SelectItem>
                      <SelectItem value="aggressive">Aggressive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Investment Experience</Label>
                  <Input {...register('finance.investment_experience')} placeholder="2 years in mutual funds" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  )
}
