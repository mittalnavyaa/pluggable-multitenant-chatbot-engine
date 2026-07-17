import { useEffect, useRef } from 'react';

export function LivePreview({ product, branding }) {
  const chatbotRef = useRef(null);

  useEffect(() => {
    if (chatbotRef.current && branding) {
      // Pass the updated branding object to the chatbot widget dynamically
      chatbotRef.current.setConfiguration({
        branding: branding
      });
    }
  }, [branding]);

  return (
    <div className="preview-viewport" style={{
      position: 'relative',
      width: '100%',
      height: '540px',
      border: '1px solid var(--color-border, #e2e8f0)',
      borderRadius: '12px',
      backgroundColor: '#f8fafc',
      overflow: 'hidden',
      transform: 'translate3d(0, 0, 0)', // Containing block isolates fixed position children inside!
      boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      {/* Mock client site mockup */}
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }}></span>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#eab308' }}></span>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e' }}></span>
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', background: '#f1f5f9', padding: '2px 8px', borderRadius: '12px' }}>
            http://acmecorp.com/preview
          </div>
        </div>
        
        <div style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '12px', marginBottom: '16px' }}>
          <h4 style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#0f172a', fontWeight: 600 }}>Acme Corp Portal</h4>
          <p style={{ margin: 0, fontSize: '11px', color: '#64748b' }}>Live customer preview view</p>
        </div>

        <p style={{ fontSize: '12px', color: '#475569', lineHeight: '1.5', margin: '0 0 16px 0' }}>
          This sandbox container simulates how the floating chatbot appears in the bottom corner of your website. Modify branding fields on the left to see live visual updates immediately.
        </p>

        <div style={{
          height: '180px',
          background: 'rgba(37, 99, 235, 0.03)',
          borderRadius: '8px',
          border: '1px dashed rgba(37, 99, 235, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          color: '#2563eb',
          fontSize: '12px'
        }}>
          <span style={{ fontWeight: 500 }}>Website Content Sandbox</span>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Widget position and theme apply dynamically inside here</span>
        </div>
      </div>

      {/* Embedded production chatbot element */}
      <envoy-chatbot
        ref={chatbotRef}
        data-bot-id={product.id}
        data-api-base={window.location.origin}
      />
    </div>
  );
}
