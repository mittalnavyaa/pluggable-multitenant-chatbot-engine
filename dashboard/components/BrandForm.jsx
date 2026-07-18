import { useState, useEffect } from 'react';

export function BrandForm({ product, bot, onPreviewChange, onSaveSuccess }) {
  const branding = bot ? (bot.branding || {}) : (product.branding || {});

  const [colors, setColors] = useState(branding.colors || {});
  const [typography, setTypography] = useState(branding.typography || {});
  const [layout, setLayout] = useState(branding.layout || {});
  const [assets, setAssets] = useState(branding.assets || {});
  const [content, setContent] = useState(branding.content || {});
  const [featureFlags, setFeatureFlags] = useState(branding.featureFlags || {});
  const [overflowMenu, setOverflowMenu] = useState(branding.overflowMenu || []);
  const [theme, setTheme] = useState(branding.theme || 'auto');

  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });
  const [menuJsonText, setMenuJsonText] = useState(JSON.stringify(branding.overflowMenu || [], null, 2));

  // Sync state when active product or bot changes
  useEffect(() => {
    const b = bot ? (bot.branding || {}) : (product.branding || {});
    setColors(b.colors || {});
    setTypography(b.typography || {});
    setLayout(b.layout || {});
    setAssets(b.assets || {});
    setContent(b.content || {});
    setFeatureFlags(b.featureFlags || {});
    setOverflowMenu(b.overflowMenu || []);
    setTheme(b.theme || 'auto');
    setMenuJsonText(JSON.stringify(b.overflowMenu || [], null, 2));
    setStatus({ type: '', message: '' });
  }, [product, bot]);

  const propagatePreview = (updatedFields) => {
    const currentConfig = {
      colors,
      typography,
      layout,
      assets,
      content,
      featureFlags,
      overflowMenu,
      theme,
      ...updatedFields
    };
    if (onPreviewChange) {
      onPreviewChange(currentConfig);
    }
  };

  const handleColorChange = (key, value) => {
    const newColors = { ...colors, [key]: value };
    setColors(newColors);
    propagatePreview({ colors: newColors });
  };

  const handleLayoutChange = (key, value) => {
    const newLayout = { ...layout, [key]: value };
    setLayout(newLayout);
    propagatePreview({ layout: newLayout });
  };

  const handlePositionChange = (key, value) => {
    const pos = layout.position || { anchor: 'bottom-right', offsetX: 20, offsetY: 20 };
    const newPos = { ...pos, [key]: value };
    const newLayout = { ...layout, position: newPos };
    setLayout(newLayout);
    propagatePreview({ layout: newLayout });
  };

  const handleContentChange = (key, value) => {
    const newContent = { ...content, [key]: value };
    setContent(newContent);
    propagatePreview({ content: newContent });
  };

  const handleSuggestedQuestionsChange = (text) => {
    const questions = text.split('\n').map(q => q.trim()).filter(q => q.length > 0);
    const newContent = { ...content, suggestedQuestions: questions };
    setContent(newContent);
    propagatePreview({ content: newContent });
  };

  const handleAssetChange = (key, value) => {
    const newAssets = { ...assets, [key]: value };
    setAssets(newAssets);
    propagatePreview({ assets: newAssets });
  };

  const handleMenuJsonChange = (text) => {
    setMenuJsonText(text);
    try {
      const parsed = JSON.parse(text);
      if (Array.isArray(parsed)) {
        setOverflowMenu(parsed);
        propagatePreview({ overflowMenu: parsed });
        setStatus({ type: '', message: '' });
      }
    } catch (e) {
      // Keep state, but don't propagate malformed JSON
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatus({ type: '', message: '' });

    // Validate overflow menu JSON before saving
    let parsedMenu = overflowMenu;
    try {
      parsedMenu = JSON.parse(menuJsonText);
      if (!Array.isArray(parsedMenu)) {
        throw new Error("Overflow menu must be a JSON array.");
      }
    } catch (err) {
      setStatus({ type: 'error', message: 'Invalid Overflow Menu JSON configuration.' });
      setSaving(false);
      return;
    }

    const payload = {
      colors,
      typography,
      layout: {
        ...layout,
        position: layout.position || { anchor: 'bottom-right', offsetX: 20, offsetY: 20 }
      },
      assets,
      content,
      featureFlags,
      overflowMenu: parsedMenu,
      theme
    };

    try {
      const isBot = !!bot;
      const url = isBot 
        ? `/api/v1/bots/${bot.id}/branding` 
        : `/api/v1/products/${product.uuid || product.id}/branding`;

      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setStatus({ type: 'success', message: 'Branding configurations saved successfully!' });
        if (onSaveSuccess) {
          onSaveSuccess();
        }
      } else {
        const err = await response.json();
        setStatus({ type: 'error', message: err.detail || 'Failed to save branding configurations.' });
      }
    } catch (err) {
      setStatus({ type: 'error', message: 'Network error. Failed to connect to server.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="brand-form" onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {status.message && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '13px',
          fontWeight: 500,
          background: status.type === 'success' ? '#def7ec' : '#fde8e8',
          color: status.type === 'success' ? '#03543f' : '#9b1c1c',
          border: `1px solid ${status.type === 'success' ? '#bcf0da' : '#f8b4b4'}`
        }}>
          {status.message}
        </div>
      )}

      {/* Group 1: General Info */}
      <div style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--color-text)' }}>General Settings</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <label>
            Bot Name
            <input 
              type="text" 
              value={content.widgetTitle || ''} 
              onChange={(e) => handleContentChange('widgetTitle', e.target.value)} 
            />
          </label>
          <label>
            Subtitle
            <input 
              type="text" 
              value={content.subtitle || ''} 
              onChange={(e) => handleContentChange('subtitle', e.target.value)} 
            />
          </label>
          <label style={{ gridColumn: 'span 2' }}>
            Welcome Message
            <textarea 
              value={content.welcomeMessage || ''} 
              onChange={(e) => handleContentChange('welcomeMessage', e.target.value)}
              rows="2" 
            />
          </label>
          <label>
            Default Theme Mode
            <select 
              value={theme} 
              onChange={(e) => {
                setTheme(e.target.value);
                propagatePreview({ theme: e.target.value });
              }}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
                color: 'var(--color-text)'
              }}
            >
              <option value="auto">Auto (Match System Preferences)</option>
              <option value="light">Always Light Mode</option>
              <option value="dark">Always Dark Mode</option>
            </select>
          </label>
        </div>
      </div>

      {/* Group 2: Colors */}
      <div style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--color-text)' }}>Light Theme Colors</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          <label style={{ fontSize: '11px' }}>
            Primary
            <input type="color" value={colors.primaryColor || '#2563EB'} onChange={(e) => handleColorChange('primaryColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Secondary
            <input type="color" value={colors.secondaryColor || '#475569'} onChange={(e) => handleColorChange('secondaryColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Background
            <input type="color" value={colors.backgroundColor || '#f8fafc'} onChange={(e) => handleColorChange('backgroundColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Text
            <input type="color" value={colors.textColor || '#111827'} onChange={(e) => handleColorChange('textColor', e.target.value)} />
          </label>
        </div>

        <h3 style={{ margin: '16px 0 12px 0', fontSize: '14px', color: 'var(--color-text)' }}>Dark Theme Colors</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          <label style={{ fontSize: '11px' }}>
            Primary (Dark)
            <input type="color" value={colors.darkPrimaryColor || '#3b82f6'} onChange={(e) => handleColorChange('darkPrimaryColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Secondary (Dark)
            <input type="color" value={colors.darkSecondaryColor || '#64748b'} onChange={(e) => handleColorChange('darkSecondaryColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Background (Dark)
            <input type="color" value={colors.darkBackgroundColor || '#020617'} onChange={(e) => handleColorChange('darkBackgroundColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Text (Dark)
            <input type="color" value={colors.darkTextColor || '#f8fafc'} onChange={(e) => handleColorChange('darkTextColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Surface (Dark)
            <input type="color" value={colors.darkSurfaceColor || '#0f172a'} onChange={(e) => handleColorChange('darkSurfaceColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Border (Dark)
            <input type="color" value={colors.darkBorderColor || '#334155'} onChange={(e) => handleColorChange('darkBorderColor', e.target.value)} />
          </label>
          <label style={{ fontSize: '11px' }}>
            Muted Text (Dark)
            <input type="color" value={colors.darkMutedTextColor || '#94a3b8'} onChange={(e) => handleColorChange('darkMutedTextColor', e.target.value)} />
          </label>
        </div>
      </div>

      {/* Group 3: Layout & Position */}
      <div style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--color-text)' }}>Layout & Position</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          <label>
            Position Anchor
            <select 
              value={layout.position?.anchor || 'bottom-right'} 
              onChange={(e) => handlePositionChange('anchor', e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
                color: 'var(--color-text)'
              }}
            >
              <option value="bottom-right">Bottom Right</option>
              <option value="bottom-left">Bottom Left</option>
              <option value="top-right">Top Right</option>
              <option value="top-left">Top Left</option>
            </select>
          </label>
          <label>
            Offset X (px)
            <input 
              type="number" 
              value={layout.position?.offsetX ?? 20} 
              onChange={(e) => handlePositionChange('offsetX', parseInt(e.target.value) || 0)} 
            />
          </label>
          <label>
            Offset Y (px)
            <input 
              type="number" 
              value={layout.position?.offsetY ?? 20} 
              onChange={(e) => handlePositionChange('offsetY', parseInt(e.target.value) || 0)} 
            />
          </label>
          <label>
            Border Radius
            <input 
              type="text" 
              value={layout.borderRadius || '12px'} 
              onChange={(e) => handleLayoutChange('borderRadius', e.target.value)} 
            />
          </label>
          <label>
            Width (e.g. 380px)
            <input 
              type="text" 
              value={layout.chatWidth || '380px'} 
              onChange={(e) => handleLayoutChange('chatWidth', e.target.value)} 
            />
          </label>
          <label>
            Height (e.g. 520px)
            <input 
              type="text" 
              value={layout.chatHeight || '520px'} 
              onChange={(e) => handleLayoutChange('chatHeight', e.target.value)} 
            />
          </label>
        </div>
      </div>

      {/* Group 4: Ingestion Assets & Suggestions */}
      <div style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--color-text)' }}>Assets & Suggested Questions</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <label>
            Logo URL
            <input 
              type="url" 
              value={assets.companyLogo || ''} 
              onChange={(e) => handleAssetChange('companyLogo', e.target.value)} 
            />
          </label>
          <label>
            Bot Avatar URL
            <input 
              type="url" 
              value={assets.botAvatar || ''} 
              onChange={(e) => handleAssetChange('botAvatar', e.target.value)} 
            />
          </label>
          <label>
            Launcher Icon URL
            <input 
              type="url" 
              value={assets.launcherIcon || ''} 
              onChange={(e) => handleAssetChange('launcherIcon', e.target.value)} 
            />
          </label>
          <label>
            Suggested Questions (One question per line)
            <textarea 
              value={(content.suggestedQuestions || []).join('\n')} 
              onChange={(e) => handleSuggestedQuestionsChange(e.target.value)}
              rows="3" 
            />
          </label>
        </div>
      </div>

      {/* Group 5: Overflow Menu JSON */}
      <div style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
        <h3 style={{ margin: '0 0 4px 0', fontSize: '14px', color: 'var(--color-text)' }}>Overflow Menu Configuration</h3>
        <p style={{ margin: '0 0 10px 0', fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Configure headers dropdown operations in valid JSON list array.
        </p>
        <label>
          JSON Array Config
          <textarea 
            value={menuJsonText} 
            onChange={(e) => handleMenuJsonChange(e.target.value)}
            rows="5"
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        </label>
      </div>

      {/* Actions */}
      <div className="brand-form__actions" style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '10px' }}>
        <button 
          className="button button--secondary" 
          type="button"
          onClick={() => propagatePreview({})}
        >
          Force Preview Reset
        </button>
        <button 
          className="button" 
          type="submit"
          disabled={saving}
          style={{ cursor: saving ? 'not-allowed' : 'pointer' }}
        >
          {saving ? 'Saving Config...' : 'Save Configuration'}
        </button>
      </div>
    </form>
  );
}
