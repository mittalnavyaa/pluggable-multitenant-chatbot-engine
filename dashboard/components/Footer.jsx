export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="dashboard-footer" role="contentinfo">
      <div className="dashboard-footer__inner">
        <div className="dashboard-footer__brand">
          <span className="dashboard-footer__mark">AI</span>
          <span className="dashboard-footer__name">Chatbot Platform</span>
        </div>
        <p className="dashboard-footer__copy">
          &copy; {year} Enterprise AI Chatbot Platform. Internal use only.
        </p>
        <p className="dashboard-footer__version">v2026.07.06</p>
      </div>
    </footer>
  );
}
