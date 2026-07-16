import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { useQueryClient } from '@tanstack/react-query'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Save, User, Briefcase, Heart, DollarSign } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'
import { authService, getErrorMessage, profileService } from '@/services'
import { useProfile, queryKeys, invalidateProfileDependentQueries } from '@/hooks'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
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
    education: z.string().optional(),
    current_skills: z.string().optional(),
    target_role: z.string().optional(),
    experience_level: z.string().optional(),
    career_goal: z.string().optional(),
    preferred_roles: z.string().optional(),
    resume: z.string().optional(),
  }).optional(),
  health: z.object({
    medical_conditions: z.string().optional(),
    lifestyle: z.string().optional(),
    fitness_goal: z.string().optional(),
    sleep_hours: z.coerce.number().optional(),
    sleep_quality: z.coerce.number().optional(),
    diet_preference: z.string().optional(),
    workout: z.string().optional(),
    health_goals: z.string().optional(),
    water_intake: z.coerce.number().optional(),
  }).optional(),
  finance: z.object({
    monthly_income: z.coerce.number().optional(),
    monthly_expenses: z.coerce.number().optional(),
    savings_goal: z.coerce.number().optional(),
    investments: z.string().optional(),
    risk_appetite: z.string().optional(),
    investment_experience: z.string().optional(),
    financial_goals: z.string().optional(),
    budget: z.string().optional(),
  }).optional(),
})

type ProfileForm = z.infer<typeof profileSchema>

function buildProfilePayload(data: ProfileForm): FullProfile {
  return {
    general: data.general ? {
      age: data.general.age,
      gender: data.general.gender,
      height_cm: data.general.height_cm,
      weight_kg: data.general.weight_kg,
      location: data.general.location,
    } : undefined,
    career: data.career ? {
      education: data.career.education,
      current_skills: data.career.current_skills?.split(',').map((skill) => skill.trim()).filter(Boolean),
      target_role: data.career.target_role,
      experience_level: data.career.experience_level,
      career_goal: data.career.career_goal,
      preferred_roles: data.career.preferred_roles,
      resume: data.career.resume,
    } : undefined,
    health: data.health ? {
      medical_conditions: data.health.medical_conditions,
      lifestyle: data.health.lifestyle,
      fitness_goal: data.health.fitness_goal,
      sleep_hours: data.health.sleep_hours,
      sleep_quality: data.health.sleep_quality,
      diet_preference: data.health.diet_preference,
      workout: data.health.workout,
      health_goals: data.health.health_goals,
      water_intake: data.health.water_intake,
    } : undefined,
    finance: data.finance ? {
      monthly_income: data.finance.monthly_income,
      monthly_expenses: data.finance.monthly_expenses,
      savings_goal: data.finance.savings_goal,
      investments: data.finance.investments,
      risk_appetite: data.finance.risk_appetite,
      investment_experience: data.finance.investment_experience,
      financial_goals: data.finance.financial_goals,
      budget: data.finance.budget,
    } : undefined,
  }
}

function buildFormValues(profile: FullProfile | undefined, userName: string): ProfileForm {
  if (!profile) {
    return {
      name: userName,
      general: {},
      career: {},
      health: {},
      finance: {},
    }
  }

  return {
    name: userName,
    general: profile.general ? {
      age: profile.general.age,
      gender: profile.general.gender,
      height_cm: profile.general.height_cm,
      weight_kg: profile.general.weight_kg,
      location: profile.general.location,
    } : {},
    career: profile.career ? {
      education: profile.career.education,
      current_skills: profile.career.current_skills?.join(', '),
      target_role: profile.career.target_role,
      experience_level: profile.career.experience_level,
      career_goal: profile.career.career_goal,
      preferred_roles: profile.career.preferred_roles,
      resume: profile.career.resume,
    } : {},
    health: profile.health ? {
      medical_conditions: profile.health.medical_conditions,
      lifestyle: profile.health.lifestyle,
      fitness_goal: profile.health.fitness_goal,
      sleep_hours: profile.health.sleep_hours,
      sleep_quality: profile.health.sleep_quality,
      diet_preference: profile.health.diet_preference,
      workout: profile.health.workout,
      health_goals: profile.health.health_goals,
      water_intake: profile.health.water_intake,
    } : {},
    finance: profile.finance ? {
      monthly_income: profile.finance.monthly_income,
      monthly_expenses: profile.finance.monthly_expenses,
      savings_goal: profile.finance.savings_goal,
      investments: profile.finance.investments,
      risk_appetite: profile.finance.risk_appetite,
      investment_experience: profile.finance.investment_experience,
      financial_goals: profile.finance.financial_goals,
      budget: profile.finance.budget,
    } : {},
  }
}

export function ProfilePage() {
  const { user, setUser } = useAuth()
  const { t } = useLanguage()
  const queryClient = useQueryClient()
  const { data: profile, isLoading, refetch } = useProfile()

  const { register, control, handleSubmit, reset, formState: { isSubmitting } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || '',
      general: {},
      career: {},
      health: {},
      finance: {},
    },
  })
  const initializedRef = useRef(false)
  const [hasProfile, setHasProfile] = useState(false)

  const profileHasData = useMemo(() => {
    if (!profile) return false
    return [profile.general, profile.career, profile.health, profile.finance]
      .some((section) => !!section && Object.keys(section).length > 0)
  }, [profile])

  useEffect(() => {
    setHasProfile(profileHasData)
  }, [profileHasData])

  useEffect(() => {
    if (isLoading || initializedRef.current) return
    initializedRef.current = true
    reset(buildFormValues(profile, user?.name || ''))
  }, [isLoading, profile, reset, user?.name])

  useEffect(() => {
    if (!user?.id || initializedRef.current) return
    void refetch()
  }, [refetch, user?.id])

  const onSubmit = async (data: ProfileForm) => {
    const payload = buildProfilePayload(data)
    const saveError = 'Unable to save profile right now.'

    setIsSaving(true)
    setSaveMessage(null)

    try {
      if (data.name && data.name !== user?.name) {
        const updatedUser = await authService.updateCurrentUser(data.name)
        authService.saveUser(updatedUser)
        setUser(updatedUser)
      }

      const savedProfile = hasProfile
        ? await profileService.update(payload)
        : await profileService.create(payload)

      if (savedProfile) {
        const refreshedProfile = await profileService.get()
        setHasProfile(true)
        queryClient.setQueryData(queryKeys.profile, refreshedProfile)
        await invalidateProfileDependentQueries(queryClient)
        await refetch()
        reset(buildFormValues(refreshedProfile, data.name || user?.name || ''))
        setIsSaved(true)
        setSaveMessage(t('profileSaved'))
        toast.success(t('profileSaved'))
      }
    } catch (err) {
      const message = getErrorMessage(err) || saveError
      setSaveMessage(message)
      setIsSaved(false)
      toast.error(message)
    } finally {
      setIsSaving(false)
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
      toast.success(t('avatarDeleted'))
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [isSaved, setIsSaved] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const initials = user?.name?.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2) || 'U'
  const isBusy = isSaving || isSubmitting

  if (isLoading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <PageHeader
        title="Profile"
        description="Manage your personal and domain-specific details"
        action={
          <Button type="submit" variant="gradient" form="profileForm" disabled={isBusy}>
            {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save Changes
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
              {user?.avatar_url ? (
                <Button variant="outline" size="sm" onClick={handleAvatarRemove}>
                  {t('deleteAvatar')}
                </Button>
              ) : null}
            </div>
          </div>
        </CardContent>
      </Card>
      {saveMessage ? (
        <div className={`rounded-lg border px-4 py-3 text-sm ${isSaved ? 'border-green-200 bg-green-50 text-green-900' : 'border-red-200 bg-red-50 text-red-900'}`}>
          {saveMessage}
        </div>
      ) : null}

      <form id="profileForm" onSubmit={handleSubmit(onSubmit)}>
        <Tabs defaultValue="general" onValueChange={() => setSaveMessage(null)}>
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
                  <Input {...register('name')} />
                </div>
                <div className="space-y-2">
                  <Label>Age</Label>
                  <Input type="number" {...register('general.age')} />
                </div>
                <div className="space-y-2">
                  <Label>Gender</Label>
                  <Input {...register('general.gender')} />
                </div>
                <div className="space-y-2">
                  <Label>Height (cm)</Label>
                  <Input type="number" {...register('general.height_cm')} />
                </div>
                <div className="space-y-2">
                  <Label>Weight (kg)</Label>
                  <Input type="number" {...register('general.weight_kg')} />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Location</Label>
                  <Input {...register('general.location')} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="career">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Briefcase className="h-4 w-4" /> Career Details
                </CardTitle>
                <CardDescription>Education, skills, and role preferences</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Education</Label>
                  <Input {...register('career.education')} placeholder="e.g. B.Sc. Computer Science" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Current Skills</Label>
                  <Input {...register('career.current_skills')} placeholder="Python, SQL, Leadership" />
                </div>
                <div className="space-y-2">
                  <Label>Target Role</Label>
                  <Input {...register('career.target_role')} placeholder="e.g. Product Manager" />
                </div>
                <div className="space-y-2">
                  <Label>Experience Level</Label>
                  <Controller
                    control={control}
                    name="career.experience_level"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select experience" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="intern">Intern</SelectItem>
                          <SelectItem value="entry">Entry</SelectItem>
                          <SelectItem value="junior">Junior</SelectItem>
                          <SelectItem value="mid">Mid</SelectItem>
                          <SelectItem value="senior">Senior</SelectItem>
                          <SelectItem value="lead">Lead</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Career Goal</Label>
                  <Controller
                    control={control}
                    name="career.career_goal"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choose a goal" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="management">Management</SelectItem>
                          <SelectItem value="specialist">Specialist Expertise</SelectItem>
                          <SelectItem value="startup">Startup Founder</SelectItem>
                          <SelectItem value="freelance">Freelance</SelectItem>
                          <SelectItem value="reskill">Reskill / Career Change</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Preferred Roles</Label>
                  <Input {...register('career.preferred_roles')} placeholder="e.g. Product Owner, UX Designer" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Resume</Label>
                  <Textarea {...register('career.resume')} placeholder="Paste resume summary or profile description" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="health">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Heart className="h-4 w-4" /> Health Details
                </CardTitle>
                <CardDescription>Medical, lifestyle, and wellness preferences</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label>Medical Conditions</Label>
                  <Textarea {...register('health.medical_conditions')} placeholder="e.g. asthma, allergies" />
                </div>
                <div className="space-y-2">
                  <Label>Lifestyle</Label>
                  <Controller
                    control={control}
                    name="health.lifestyle"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select lifestyle" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="sedentary">Sedentary</SelectItem>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="very_active">Very Active</SelectItem>
                          <SelectItem value="athletic">Athletic</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Sleep Hours</Label>
                  <Input type="number" step="0.5" min="0" {...register('health.sleep_hours')} />
                </div>
                <div className="space-y-2">
                  <Label>Sleep Quality</Label>
                  <Controller
                    control={control}
                    name="health.sleep_quality"
                    render={({ field }) => (
                      <Select value={field.value?.toString() || ''} onValueChange={(value) => field.onChange(value ? Number(value) : undefined)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Rate 1-10" />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.from({ length: 10 }, (_, index) => (
                            <SelectItem key={index + 1} value={(index + 1).toString()}>{index + 1}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Diet</Label>
                  <Controller
                    control={control}
                    name="health.diet_preference"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choose diet" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">No Preference</SelectItem>
                          <SelectItem value="vegetarian">Vegetarian</SelectItem>
                          <SelectItem value="vegan">Vegan</SelectItem>
                          <SelectItem value="pescatarian">Pescatarian</SelectItem>
                          <SelectItem value="keto">Keto</SelectItem>
                          <SelectItem value="mediterranean">Mediterranean</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Workout</Label>
                  <Input {...register('health.workout')} placeholder="e.g. gym, yoga, cycling" />
                </div>
                <div className="space-y-2">
                  <Label>Goals</Label>
                  <Input {...register('health.health_goals')} placeholder="e.g. lose weight, build strength" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Water Intake (liters/day)</Label>
                  <Input type="number" step="0.25" min="0" {...register('health.water_intake')} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="finance">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <DollarSign className="h-4 w-4" /> Finance Details
                </CardTitle>
                <CardDescription>Income, savings, and investment preferences</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Monthly Income</Label>
                  <Input type="number" step="0.01" min="0" {...register('finance.monthly_income')} />
                </div>
                <div className="space-y-2">
                  <Label>Monthly Expenses</Label>
                  <Input type="number" step="0.01" min="0" {...register('finance.monthly_expenses')} />
                </div>
                <div className="space-y-2">
                  <Label>Savings Goal</Label>
                  <Input type="number" step="0.01" min="0" {...register('finance.savings_goal')} />
                </div>
                <div className="space-y-2">
                  <Label>Investments</Label>
                  <Input {...register('finance.investments')} placeholder="e.g. stocks, real estate" />
                </div>
                <div className="space-y-2">
                  <Label>Risk Tolerance</Label>
                  <Controller
                    control={control}
                    name="finance.risk_appetite"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select risk" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Investment Experience</Label>
                  <Controller
                    control={control}
                    name="finance.investment_experience"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select experience" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="beginner">Beginner</SelectItem>
                          <SelectItem value="intermediate">Intermediate</SelectItem>
                          <SelectItem value="advanced">Advanced</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Financial Goals</Label>
                  <Textarea {...register('finance.financial_goals')} placeholder="e.g. buy a house, retirement" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Budget</Label>
                  <Textarea {...register('finance.budget')} placeholder="Monthly or annual budget notes" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  )
}
