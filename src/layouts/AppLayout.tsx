import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar, getSidebarWidth } from '@/components/layout/Sidebar'
import { Navbar } from '@/components/layout/Navbar'

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const sidebarWidth = getSidebarWidth(collapsed)

  return (
    <div className="min-h-screen mesh-bg">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <Navbar sidebarWidth={sidebarWidth} />
      <main
        style={{ marginLeft: sidebarWidth, paddingTop: 64 }}
        className="min-h-screen transition-[margin-left] duration-200"
      >
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
