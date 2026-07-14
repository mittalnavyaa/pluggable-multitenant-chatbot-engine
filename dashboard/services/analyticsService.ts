// dashboard/services/analyticsService.ts

export interface KnowledgeMetrics {
  total_chunks: number;
  total_vectors: number;
  average_chunks_per_document: number;
  total_storage_bytes: number;
  validation_success_rate_percent: number;
  vectorization_success_rate_percent: number;
  average_processing_time_ms: number;
  average_embedding_time_ms: number;
  queue_length: number;
}

export interface ActivityLog {
  id: string;
  timestamp: string;
  document_name: string;
  product_id: string;
  event_type: string;
  description: string;
}

export interface ConversationVolume {
  timestamp: string;
  conversation_count: number;
  message_count: number;
}

export interface ResolutionRate {
  total_conversations: number;
  resolved_conversations: number;
  resolution_rate_percent: number;
}

export interface IntentDistribution {
  intent: string;
  count: number;
}

export interface SalesLead {
  session_id: string;
  platform_id: string;
  bot_id: string | null;
  intent: string;
  lead_status: string | null;
  first_message_at: string;
  total_token_usage: number;
}

export interface SalesLeadsResponse {
  total_leads: number;
  leads: SalesLead[];
}

export interface PlatformSummary {
  platform_id: string;
  bot_id: string | null;
  total_conversations: number;
  total_messages: number;
  average_latency_ms: number;
  resolved_conversations: number;
  sales_leads: number;
}

export interface WsStatus {
  active_connections: number;
  messages_sent: number;
  failed_broadcasts: number;
  reconnect_count: number;
  disconnect_count: number;
  average_broadcast_latency_ms: number;
}

export interface BotInfo {
  id: string;
  name: string;
  product_id: string;
  description: string | null;
}

// Fetch bot details to map bot_id to product_id for client-side tenant filtering
export async function fetchBots(): Promise<BotInfo[]> {
  const response = await fetch('/api/v1/bots');
  if (!response.ok) {
    throw new Error(`Failed to fetch bots list: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchKnowledgeMetrics(headers?: Record<string, string>): Promise<KnowledgeMetrics> {
  const response = await fetch('/api/v1/analytics/knowledge-metrics', { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch knowledge metrics: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchActivityLog(headers?: Record<string, string>): Promise<ActivityLog[]> {
  const response = await fetch('/api/v1/analytics/activity', { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch activity log: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchConversationVolume(
  params: { start_date?: string; end_date?: string; by_hour?: boolean },
  headers?: Record<string, string>
): Promise<ConversationVolume[]> {
  const query = new URLSearchParams();
  if (params.start_date) query.append('start_date', params.start_date);
  if (params.end_date) query.append('end_date', params.end_date);
  if (params.by_hour !== undefined) query.append('by_hour', String(params.by_hour));

  const url = `/api/v1/analytics/conversation-volume?${query.toString()}`;
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch conversation volume: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchResolutionRate(
  params: { start_date?: string },
  headers?: Record<string, string>
): Promise<ResolutionRate> {
  const query = new URLSearchParams();
  if (params.start_date) query.append('start_date', params.start_date);

  const url = `/api/v1/analytics/resolution-rate?${query.toString()}`;
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch resolution rate: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchIntentDistribution(
  params: { start_date?: string },
  headers?: Record<string, string>
): Promise<IntentDistribution[]> {
  const query = new URLSearchParams();
  if (params.start_date) query.append('start_date', params.start_date);

  const url = `/api/v1/analytics/intent-distribution?${query.toString()}`;
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch intent distribution: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchSalesLeads(
  params: { status?: string },
  headers?: Record<string, string>
): Promise<SalesLeadsResponse> {
  const query = new URLSearchParams();
  if (params.status) query.append('status', params.status);

  const url = `/api/v1/analytics/sales-leads?${query.toString()}`;
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch sales leads: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchPlatformSummary(headers?: Record<string, string>): Promise<PlatformSummary[]> {
  const response = await fetch('/api/v1/analytics/platform-summary', { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch platform summary: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchWsStatus(): Promise<WsStatus> {
  const response = await fetch('/api/v1/analytics/ws-status');
  if (!response.ok) {
    throw new Error(`Failed to fetch WebSocket status: HTTP ${response.status}`);
  }
  return response.json();
}

export async function triggerRefreshRollups(hoursBack: number = 24): Promise<{ success: boolean }> {
  const response = await fetch(`/api/v1/analytics/refresh-rollups?hours_back=${hoursBack}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to trigger rollup refresh: HTTP ${response.status}`);
  }
  return response.json();
}

export async function triggerCleanup(retentionDays: number = 90): Promise<{ success: boolean }> {
  const response = await fetch(`/api/v1/analytics/cleanup?retention_days=${retentionDays}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to trigger telemetry cleanup: HTTP ${response.status}`);
  }
  return response.json();
}
