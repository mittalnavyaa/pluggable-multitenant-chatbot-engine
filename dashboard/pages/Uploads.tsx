import { useEffect, useState } from 'react';
import { DetailsModal } from '../components/upload/DetailsModal';
import { DropZone } from '../components/upload/DropZone';
import { PipelineTracker } from '../components/upload/PipelineTracker';
import { UploadButton } from '../components/upload/UploadButton';
import { UploadHistoryTable } from '../components/upload/UploadHistoryTable';
import { UploadList } from '../components/upload/UploadList';
import { usePipeline } from '../hooks/usePipeline';
import { useUpload } from '../hooks/useUpload';
import { getOutputDownloadUrl } from '../services/pipelineService';
import { fetchBots, createBot, type BotInfo } from '../services/botService';
import { useEnterpriseDashboardData } from '../hooks/useEnterpriseDashboardData.js';
import '../styles/upload.css';

export function Uploads() {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [bots, setBots] = useState<BotInfo[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<string>('');
  
  // Create Bot Modal State
  const [createBotOpen, setCreateBotOpen] = useState(false);
  const [newBotName, setNewBotName] = useState('');
  const [newBotProduct, setNewBotProduct] = useState('');
  const [newBotDesc, setNewBotDesc] = useState('');

  const { products, refreshDocuments, refreshSummary } = useEnterpriseDashboardData();

  useEffect(() => {
    async function loadBots() {
      try {
        const list = await fetchBots();
        setBots(list);
      } catch (err) {
        console.error('Failed to load bots:', err);
      }
    }
    loadBots();
  }, []);

  // Initialize newBotProduct to the first product on load
  useEffect(() => {
    if (products && products.length > 0 && !newBotProduct) {
      setNewBotProduct(products[0].id);
    }
  }, [products, newBotProduct]);

  const {
    files,
    activeFile,
    addFiles,
    removeFile,
    retryUpload,
    startUpload,
    startAllUploads,
    syncPipelineStatus,
    setActiveFileId
  } = useUpload();

  const { job, loading, pollError } = usePipeline(activeFile?.jobId, activeFile?.fileName);

  useEffect(() => {
    if (activeFile && job) {
      syncPipelineStatus(activeFile.id, job.status);
      if (job.status === 'ready' || job.status === 'failed') {
        refreshDocuments?.();
      }
    }
  }, [activeFile, job, syncPipelineStatus, refreshDocuments]);

  // Refetch documents list when local file uploading status transitions occur
  useEffect(() => {
    refreshDocuments?.();
  }, [files, refreshDocuments]);

  const handleCreateBotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBotName.trim() || !newBotProduct) return;
    try {
      const newBot = await createBot(newBotName, newBotProduct, newBotDesc);
      const list = await fetchBots();
      setBots(list);
      setSelectedBotId(newBot.id); // Auto-select the newly created bot
      refreshSummary?.(); // Refresh metrics when a bot is created
      setCreateBotOpen(false);
      setNewBotName('');
      setNewBotDesc('');
    } catch (err) {
      console.error('Failed to create bot:', err);
    }
  };

  const downloadUrl = job?.status === 'ready' && job.jobId ? getOutputDownloadUrl(job.jobId) : null;

  return (
    <div className="upload-page">
      <section className="upload-page__main">
        <DropZone onFilesSelected={addFiles} />

        {/* Bot Selector Panel */}
        <div className="bot-selector-card" style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: '8px',
          padding: '20px',
          display: 'grid',
          gap: '12px'
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>Bot Ingestion Context</h3>
            <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: 'var(--muted-text-color)' }}>
              Choose or create a target Bot to receive and process these documents.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <select
              value={selectedBotId}
              onChange={(e) => setSelectedBotId(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
                color: 'var(--color-text)',
                minWidth: '240px'
              }}
            >
              <option value="">-- Select Bot (Required) --</option>
              {bots.map((bot) => (
                <option key={bot.id} value={bot.id}>
                  {bot.name} ({bot.productId.toUpperCase()})
                </option>
              ))}
            </select>
            <button
              className="upload-button upload-button--secondary"
              type="button"
              onClick={() => setCreateBotOpen(true)}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: '1px solid var(--color-border)',
                background: 'transparent',
                color: 'var(--color-text)',
                cursor: 'pointer'
              }}
            >
              + Create Bot
            </button>
          </div>
          {!selectedBotId && files.length > 0 && (
            <div style={{
              color: '#b91c1c',
              fontSize: '0.8125rem',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginTop: '4px'
            }}>
              <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#b91c1c' }}></span>
              A Bot must be selected before you can perform document ingestion.
            </div>
          )}
        </div>

        <div className="upload-page__toolbar">
          <div>
            <h2>Selected Files</h2>
            <p>Files are validated locally before upload submission.</p>
          </div>
          <UploadButton
            label="Upload All Valid Files"
            onClick={() => startAllUploads(selectedBotId)}
            disabled={files.length === 0 || !selectedBotId}
          />
        </div>
        <UploadList
          files={files}
          onRemove={removeFile}
          onRetry={(fileId) => retryUpload(fileId, selectedBotId)}
          onUpload={(fileId) => startUpload(fileId, selectedBotId)}
          onSelect={setActiveFileId}
          isUploadDisabled={!selectedBotId}
        />
        <section className="upload-page__history">
          <h2>Upload History</h2>
          <UploadHistoryTable files={files} />
        </section>
      </section>
      <aside className="upload-page__side">
        <PipelineTracker job={job} loading={loading} />
        {pollError ? (
          <div className="upload-page__error">
            <strong>Connection error:</strong> {pollError}
          </div>
        ) : null}
        <div className="upload-page__side-actions">
          <button className="upload-button upload-button--secondary" type="button" onClick={() => setDetailsOpen(true)} disabled={!job}>
            View Details
          </button>
          {downloadUrl ? (
            <a className="upload-button" href={downloadUrl} download>
              Download Markdown
            </a>
          ) : null}
        </div>
      </aside>
      {detailsOpen ? <DetailsModal job={job} onClose={() => setDetailsOpen(false)} /> : null}

      {/* Create Bot Modal Dialog */}
      {createBotOpen ? (
        <div className="upload-modal" role="dialog" aria-modal="true" aria-label="Create bot">
          <div className="upload-modal__content" style={{ maxWidth: '480px' }}>
            <div className="upload-modal__header">
              <h2>Create New Bot</h2>
              <button className="upload-link-button" type="button" onClick={() => setCreateBotOpen(false)}>Close</button>
            </div>
            <form onSubmit={handleCreateBotSubmit} style={{ display: 'grid', gap: '16px' }}>
              <div style={{ display: 'grid', gap: '6px' }}>
                <label htmlFor="bot-name" style={{ fontWeight: 500, fontSize: '0.875rem' }}>Bot Name *</label>
                <input
                  id="bot-name"
                  type="text"
                  required
                  placeholder="e.g. FAQ Support Bot"
                  value={newBotName}
                  onChange={(e) => setNewBotName(e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-bg)',
                    color: 'var(--color-text)'
                  }}
                />
              </div>
              <div style={{ display: 'grid', gap: '6px' }}>
                <label htmlFor="bot-product" style={{ fontWeight: 500, fontSize: '0.875rem' }}>Product Association *</label>
                <select
                  id="bot-product"
                  required
                  value={newBotProduct}
                  onChange={(e) => setNewBotProduct(e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-bg)',
                    color: 'var(--color-text)'
                  }}
                >
                  <option value="">-- Select Product --</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gap: '6px' }}>
                <label htmlFor="bot-desc" style={{ fontWeight: 500, fontSize: '0.875rem' }}>Description (optional)</label>
                <textarea
                  id="bot-desc"
                  rows={3}
                  placeholder="Describe the bot's purpose and system context..."
                  value={newBotDesc}
                  onChange={(e) => setNewBotDesc(e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-bg)',
                    color: 'var(--color-text)',
                    resize: 'vertical'
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
                <button className="upload-link-button" type="button" onClick={() => setCreateBotOpen(false)}>Cancel</button>
                <button className="upload-button" type="submit" disabled={!newBotName.trim() || !newBotProduct}>
                  Create Bot
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
