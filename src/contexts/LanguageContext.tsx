import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { STORAGE_KEYS } from '@/utils/constants'
import type { LanguageCode } from '@/types'

const translations = {
  en: {
    welcome: 'Welcome back',
    createAccount: 'Create account',
    signIn: 'Sign in',
    register: 'Register',
    login: 'Login',
    forgotPassword: 'Forgot password?',
    resetPassword: 'Reset password',
    sendResetLink: 'Send reset link',
    accountCreated: 'Account created successfully!',
    profileSaved: 'Profile saved successfully',
    settings: 'Settings',
    notifications: 'Notifications',
    language: 'Language',
    appearance: 'Appearance',
    security: 'Security',
    twoFactorAuthentication: 'Two-factor authentication',
    changePassword: 'Change password',
    personalDetails: 'Personal Details',
    careerDetails: 'Career Details',
    healthDetails: 'Health Details',
    financeDetails: 'Financial Details',
    dashboard: 'Dashboard',
    askAI: 'Ask AI',
    memory: 'Memory',
    reports: 'Reports',
    history: 'History',
    profile: 'Profile',
    careerDashboard: 'Career Dashboard',
    healthDashboard: 'Health Dashboard',
    financeDashboard: 'Finance Dashboard',
    noConversations: 'No conversations found',
    search: 'Search',
    save: 'Save',
    uploadAvatar: 'Upload Avatar',
    deleteAvatar: 'Delete Avatar',
    avatarUploaded: 'Avatar uploaded successfully',
    avatarDeleted: 'Avatar removed successfully',
    profileImage: 'Profile Image',
    emailNotifications: 'Email notifications',
    pushNotifications: 'Push notifications',
    reportNotifications: 'Report notifications',
    aiInsights: 'AI insights',
    selectLanguage: 'Select language',
    notificationsSettings: 'Customize notification preferences',
    theme: 'Theme',
    requestSent: 'Reset link sent to your email',
    loginRedirect: 'Please login to continue',
    generateReport: 'Generate Report',
  },
  hi: {
    welcome: 'वापसी पर स्वागत है',
    createAccount: 'खाता बनाएं',
    signIn: 'साइन इन करें',
    register: 'रजिस्टर करें',
    login: 'लॉगिन',
    forgotPassword: 'पासवर्ड भूल गए?',
    resetPassword: 'पासवर्ड रीसेट करें',
    sendResetLink: 'रीसेट लिंक भेजें',
    accountCreated: 'खाता सफलतापूर्वक बनाया गया!',
    profileSaved: 'प्रोफ़ाइल सफलतापूर्वक सहेजी गई',
    settings: 'सेटिंग्स',
    notifications: 'सूचनाएँ',
    language: 'भाषा',
    appearance: 'अवस्थिति',
    security: 'सुरक्षा',
    twoFactorAuthentication: 'दो-कारक प्रमाणीकरण',
    changePassword: 'पासवर्ड बदलें',
    personalDetails: 'व्यक्तिगत विवरण',
    careerDetails: 'करियर विवरण',
    healthDetails: 'स्वास्थ्य विवरण',
    financeDetails: 'वित्तीय विवरण',
    dashboard: 'डैशबोर्ड',
    askAI: 'AI से पूछें',
    memory: 'स्मृति',
    reports: 'रिपोर्ट',
    history: 'इतिहास',
    profile: 'प्रोफ़ाइल',
    careerDashboard: 'करियर डैशबोर्ड',
    healthDashboard: 'स्वास्थ्य डैशबोर्ड',
    financeDashboard: 'वित्त डैशबोर्ड',
    noConversations: 'कोई वार्तालाप नहीं मिला',
    search: 'खोजें',
    save: 'सहेजें',
    uploadAvatar: 'अवतार अपलोड करें',
    deleteAvatar: 'अवतार हटाएं',
    avatarUploaded: 'अवतार सफलतापूर्वक अपलोड किया गया',
    avatarDeleted: 'अवतार सफलतापूर्वक हटा दिया गया',
    profileImage: 'प्रोफ़ाइल छवि',
    emailNotifications: 'ईमेल सूचनाएँ',
    pushNotifications: 'पुश सूचनाएँ',
    reportNotifications: 'रिपोर्ट सूचनाएँ',
    aiInsights: 'एआई अंतर्दृष्टि',
    selectLanguage: 'भाषा चुनें',
    notificationsSettings: 'सूचना प्राथमिकताएँ अनुकूलित करें',
    theme: 'थीम',
    requestSent: 'रीसेट लिंक आपके ईमेल पर भेजा गया',
    loginRedirect: 'कृपया जारी रखने के लिए लॉगिन करें',
    generateReport: 'रिपोर्ट बनाएं',
  },
  kn: {
    welcome: 'ಮತ್ತೆ ಸ್ವಾಗತ',
    createAccount: 'ಖಾತೆ ರಚಿಸಿ',
    signIn: 'ಸೈನ್ ಇನ್ ಮಾಡಿ',
    register: 'ನೋಂದಾಯಿಸು',
    login: 'ಲಾಗಿನ್',
    forgotPassword: 'ಪಾಸ್ವರ್ಡ್ ಮರೆತೀರಾ?',
    resetPassword: 'ಪಾಸ್ವರ್ಡ್ ಮರುಹೊಂದಿಸಿ',
    sendResetLink: 'ಮರುಹೊಂದಿಸುವ ಲಿಂಕ್ ಕಳುಹಿಸಿ',
    accountCreated: 'ಖಾತೆ ಯಶಸ್ವಿಯಾಗಿ ಸೃಷ್ಟಿಸಲಾಗಿದೆ!',
    profileSaved: 'ಪ್ರೊಫೈಲ್ ಯಶಸ್ವಿಯಾಗಿ ಉಳಿಸಲಾಗಿದೆ',
    settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    notifications: 'ಅಧಿಸೂಚನೆಗಳು',
    language: 'ಭಾಷೆ',
    appearance: 'ದೃಶ್ಯ',
    security: 'ಸುರಕ್ಷತೆ',
    twoFactorAuthentication: 'ಎರಡು-ಘಟಕ ಪರಿಶೀಲನೆ',
    changePassword: 'ಗುಪ್ತಪದ ಬದಲಾಯಿಸಿ',
    personalDetails: 'ವೈಯಕ್ತಿಕ ವಿವರಗಳು',
    careerDetails: 'ಕೆರಿಯರ್ ವಿವರಗಳು',
    healthDetails: 'ಆರೋಗ್ಯ ವಿವರಗಳು',
    financeDetails: 'ಅರ್ಥವ್ಯವಸ್ಥೆಯ ವಿವರಗಳು',
    dashboard: 'ಡ್ಯಾಶ್ಬೋರ್ಡ್',
    askAI: 'AI ಕೇಳಿ',
    memory: 'ಸ್ಮೃತಿ',
    reports: 'ರಿಪೋರ್ಟ್‌ಗಳು',
    history: 'ಇತಿಹಾಸ',
    profile: 'ಪ್ರೊಫೈಲ್',
    careerDashboard: 'ಕೆರಿಯರ್ ಡ್ಯಾಶ್ಬೋರ್ಡ್',
    healthDashboard: 'ಆರೋಗ್ಯ ಡ್ಯಾಶ್ಬೋರ್ಡ್',
    financeDashboard: 'ಆರ್ಥಿಕ ಡ್ಯಾಶ್ಬೋರ್ಡ್',
    noConversations: 'ಯಾವುದೇ ಸಂಭಾಷಣೆ ಕಂಡುಬಂದಿಲ್ಲ',
    search: 'ಹುಡುಕಿ',
    save: 'ಉಳಿಸು',
    uploadAvatar: 'ಅವತಾರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
    deleteAvatar: 'ಅವತಾರ ಅಳಿಸಿ',
    avatarUploaded: 'ಅವತಾರ ಯಶಸ್ವಿಯಾಗಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಲಾಗಿದೆ',
    avatarDeleted: 'ಅವತಾರ ಯಶಸ್ವಿಯಾಗಿ ಅಳಿಸಲಾಗಿದೆ',
    profileImage: 'ಪ್ರೊಫೈಲ್ ಚಿತ್ರ',
    emailNotifications: 'ಇಮೇಲ್ ಅಧಿಸೂಚನೆಗಳು',
    pushNotifications: 'ಪುಷ್ ಅಧಿಸೂಚನೆಗಳು',
    reportNotifications: 'ರಿಪೋರ್ಟ್ ಅಧಿಸೂಚನೆಗಳು',
    aiInsights: 'AI ಒಳನೋಟಗಳು',
    selectLanguage: 'ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    notificationsSettings: 'ಅಧಿಸೂಚನೆ ಪ್ರಾಧಾನ್ಯತೆಗಳನ್ನು ಹೊಂದಿಸಿ',
    theme: 'ಥೀಮ್',
    requestSent: 'ಮರುಹೊಂದಿಸುವ ಲಿಂಕ್ ನಿಮಗೆ ಕಳುಹಿಸಲಾಯಿತು',
    loginRedirect: 'ದಯವಿಟ್ಟು ಮುಂದುವರಿಸಲು ಲಾಗಿನ್ ಮಾಡಿ',
    generateReport: 'ರಿಪೋರ್ಟ್ ರಚಿಸಿ',
  },
}

type TranslationKeys = keyof typeof translations['en']

interface LanguageContextType {
  language: LanguageCode
  setLanguage: (lang: LanguageCode) => void
  t: (key: TranslationKeys) => string
}

const LanguageContext = createContext<LanguageContextType | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>(() => {
    return (localStorage.getItem(STORAGE_KEYS.LANGUAGE) as LanguageCode) || 'en'
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.LANGUAGE, language)
  }, [language])

  const t = (key: TranslationKeys) => {
    return translations[language]?.[key] || translations.en[key] || key
  }

  const value = useMemo(
    () => ({ language, setLanguage: setLanguageState, t }),
    [language]
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
