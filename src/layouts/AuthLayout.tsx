import { Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Sparkles } from 'lucide-react'

export function AuthLayout() {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:flex flex-col justify-between overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-12">
        <div className="absolute inset-0 mesh-bg opacity-30" />
        <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 h-96 w-96 rounded-full bg-teal-500/20 blur-3xl" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500">
              <Brain className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">TriDomain Meta-Agent</span>
          </div>
          <p className="text-slate-400 text-sm max-w-md">
            Adaptive and Explainable Multi-Domain Advisory Using RAG
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="relative z-10 space-y-8"
        >
          <div className="space-y-4">
            {[
              { title: 'Career Intelligence', desc: 'Skill gaps, roadmaps, and salary insights powered by RAG' },
              { title: 'Health Advisory', desc: 'Personalized fitness, nutrition, and wellness recommendations' },
              { title: 'Finance Planning', desc: 'Budget optimization, investment guidance, and risk profiling' },
            ].map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex items-start gap-4 rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                </div>
                <div>
                  <p className="font-medium text-white">{item.title}</p>
                  <p className="text-sm text-slate-400">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="flex items-center gap-6 text-sm text-slate-500">
            <span>3 Domains</span>
            <span>·</span>
            <span>RAG-Powered</span>
            <span>·</span>
            <span>Explainable AI</span>
          </div>
        </motion.div>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-12 bg-background">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
