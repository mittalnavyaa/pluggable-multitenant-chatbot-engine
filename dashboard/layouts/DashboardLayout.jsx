import { useState } from 'react';
import { Breadcrumb } from '../components/Breadcrumb.jsx';
import { Footer } from '../components/Footer.jsx';
import { Sidebar } from '../components/Sidebar.jsx';
import { TopNavbar } from '../components/TopNavbar.jsx';

export function DashboardLayout({ activePage, onNavigate, children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className={`dashboard-shell${collapsed ? ' dashboard-shell--collapsed' : ''}`}>
      <Sidebar
        activePage={activePage}
        onNavigate={onNavigate}
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onCollapse={() => setCollapsed((v) => !v)}
        onMobileClose={() => setMobileOpen(false)}
      />
      <div className="dashboard-main-wrap">
        <main className="dashboard-main">
          <TopNavbar
            activePage={activePage}
            onMenuClick={() => setMobileOpen((v) => !v)}
          />
          <Breadcrumb activePage={activePage} />
          {children}
        </main>
        <Footer />
      </div>
    </div>
  );
}
