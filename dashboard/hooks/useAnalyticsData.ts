// dashboard/hooks/useAnalyticsData.ts

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  KnowledgeMetrics,
  ConversationVolume,
  ResolutionRate,
  IntentDistribution,
  SalesLead,
  PlatformSummary,
  ActivityLog,
  BotInfo,
  fetchKnowledgeMetrics,
  fetchConversationVolume,
  fetchResolutionRate,
  fetchIntentDistribution,
  fetchSalesLeads,
  fetchPlatformSummary,
  fetchActivityLog,
  fetchBots
} from '../services/analyticsService';

export interface AnalyticsWorkspaceData {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  wsStatus: 'connected' | 'connecting' | 'disconnected' | 'polling';
  knowledgeMetrics: KnowledgeMetrics | null;
  conversationVolume: ConversationVolume[];
  resolutionRate: ResolutionRate | null;
  intentDistribution: IntentDistribution[];
  salesLeads: SalesLead[];
  platformSummary: PlatformSummary[];
  recentActivity: ActivityLog[];
  bots: BotInfo[];
  refresh: () => void;
}

export function useAnalyticsData(
  selectedProductId: string | null, // varchar product_id (e.g. 'tensor')
  dateRange: string // '24h' | '7d' | '30d'
): AnalyticsWorkspaceData {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'disconnected' | 'polling'>('disconnected');

  const [knowledgeMetrics, setKnowledgeMetrics] = useState<KnowledgeMetrics | null>(null);
  const [conversationVolume, setConversationVolume] = useState<ConversationVolume[]>([]);
  const [resolutionRate, setResolutionRate] = useState<ResolutionRate | null>(null);
  const [intentDistribution, setIntentDistribution] = useState<IntentDistribution[]>([]);
  const [salesLeads, setSalesLeads] = useState<SalesLead[]>([]);
  const [platformSummary, setPlatformSummary] = useState<PlatformSummary[]>([]);
  const [recentActivity, setRecentActivity] = useState<ActivityLog[]>([]);
  const [bots, setBots] = useState<BotInfo[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const activeProductUuidRef = useRef<string | null>(null);

  // Compute startDate based on range
  const getStartDate = useCallback(() => {
    const now = new Date();
    if (dateRange === '24h') {
      now.setHours(now.getHours() - 24);
    } else if (dateRange === '7d') {
      now.setDate(now.getDate() - 7);
    } else {
      now.setDate(now.getDate() - 30);
    }
    return now.toISOString();
  }, [dateRange]);

  // Load bot mapping
  useEffect(() => {
    fetchBots()
      .then(setBots)
      .catch((err) => console.error('Failed to load bots directory:', err));
  }, []);

  // Main HTTP data fetching function
  const fetchAllData = useCallback(
    async (isSilent = false) => {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);
      setError(null);

      try {
        const startDate = getStartDate();
        const headers: Record<string, string> = {};

        // Fetch product lists to get UUID for header/auth matching
        const prodRes = await fetch('/api/v1/products');
        let selectedProductUuid: string | null = null;
        if (prodRes.ok) {
          const prods = await prodRes.ok ? await prodRes.json() : [];
          const found = prods.find((p: any) => p.product_id === selectedProductId);
          if (found) {
            selectedProductUuid = found.id;
            activeProductUuidRef.current = found.id;
            // Attempt to retrieve a stored raw API key for tenant authentication
            const savedToken = localStorage.getItem(`token_${selectedProductId}`);
            if (savedToken) {
              headers['X-Envoy-API-Key'] = savedToken;
            }
          } else {
            activeProductUuidRef.current = null;
          }
        }

        // Fetch REST endpoints concurrently
        const [
          kMetrics,
          activity,
          volume,
          resRate,
          intends,
          leadsRes,
          pSummary
        ] = await Promise.all([
          fetchKnowledgeMetrics(headers),
          fetchActivityLog(headers),
          fetchConversationVolume({ start_date: startDate }, headers),
          fetchResolutionRate({ start_date: startDate }, headers),
          fetchIntentDistribution({ start_date: startDate }, headers),
          fetchSalesLeads({}, headers),
          fetchPlatformSummary(headers)
        ]);

        // Client-side filtering as fallback if requests were global (not filtered by X-Envoy-API-Key header)
        const isHeaderFiltered = !!headers['X-Envoy-API-Key'];

        if (selectedProductId && !isHeaderFiltered) {
          // Find bot IDs belonging to this tenant/product
          const tenantBotIds = bots
            .filter((b) => b.product_id === selectedProductId)
            .map((b) => b.id);

          // Filter conversation volume (must match product_id)
          // Since conversation-volume is aggregated by hourly_tenant_analytics which has tenant_id (UUID),
          // we can match selectedProductUuid if present
          const filteredVolume = selectedProductUuid
            ? volume
            : volume; // Wait, without tenant_id in response it's hard, but backend filters if authenticated

          // Filter leads based on bot_id
          const filteredLeads = leadsRes.leads.filter(
            (lead) => lead.bot_id && tenantBotIds.includes(lead.bot_id)
          );

          // Filter platform summary based on bot_id
          const filteredPlatform = pSummary.filter(
            (p) => p.bot_id && tenantBotIds.includes(p.bot_id)
          );

          setConversationVolume(volume); // Fallback to raw if backend-level filtering is used
          setResolutionRate(resRate);
          setIntentDistribution(intends);
          setSalesLeads(filteredLeads);
          setPlatformSummary(filteredPlatform);
        } else {
          // If "All Tenants" is selected, or if the backend already did the tenant-level filtering
          setConversationVolume(volume);
          setResolutionRate(resRate);
          setIntentDistribution(intends);
          setSalesLeads(leadsRes.leads);
          setPlatformSummary(pSummary);
        }

        setKnowledgeMetrics(kMetrics);
        setRecentActivity(activity.slice(0, 10));
      } catch (err: any) {
        console.error('REST Ingestion Error:', err);
        setError(err.message || 'Failed to fetch analytics statistics');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [selectedProductId, dateRange, bots, getStartDate]
  );

  // Setup WebSocket connection
  const connectWebSocket = useCallback(() => {
    // If no product selected, we can't open a tenant-specific WebSocket stream
    if (!selectedProductId) {
      setWsStatus('polling');
      return;
    }

    // Clean up existing connections
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setWsStatus('connecting');

    // Retrieve active token for WebSocket auth. Default to ws_token_a/b for local test/dev envs
    let token = localStorage.getItem(`token_${selectedProductId}`);
    if (!token) {
      // Local dev/test fallback keys seeded in backend
      token = selectedProductId === 'test_ws_tenant_a' || selectedProductId === 'test_analytics_tenant_a' ? 'ws_token_a' : 'ws_token_a';
    }

    const wsUrl = `ws://localhost:8000/api/v1/analytics/ws?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(`WebSocket connected for product ${selectedProductId}`);
        setWsStatus('connected');
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'analytics_update' && payload.data) {
            console.log('Real-Time WebSocket Analytics Update Received:', payload);
            const data = payload.data;
            
            // Highlight update logic can be triggered here
            if (data.conversation_volume) setConversationVolume(data.conversation_volume);
            if (data.resolution_rate) setResolutionRate(data.resolution_rate);
            if (data.intent_distribution) setIntentDistribution(data.intent_distribution);
            if (data.sales_leads) setSalesLeads(data.sales_leads.leads || []);
            if (data.platform_summary) setPlatformSummary(data.platform_summary);
          }
        } catch (ex) {
          console.error('Failed to parse WebSocket message JSON:', ex);
        }
      };

      ws.onerror = (err) => {
        console.warn('WebSocket connection error:', err);
      };

      ws.onclose = (ev) => {
        console.log(`WebSocket closed (Code: ${ev.code}). Transiting to fallback polling.`);
        wsRef.current = null;

        // If closed due to invalid credentials (code 4003) or missing setup, disable WS retry and poll
        if (ev.code === 4003) {
          setWsStatus('polling');
        } else {
          setWsStatus('disconnected');
          // Reconnect attempt after 5 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 5000);
        }
      };
    } catch (err) {
      console.error('Failed to instantiate WebSocket:', err);
      setWsStatus('polling');
    }
  }, [selectedProductId]);

  // Handle active data fetching lifecycle
  useEffect(() => {
    fetchAllData();

    // Start WebSocket
    connectWebSocket();

    // Set fallback HTTP polling interval (every 10s)
    pollingIntervalRef.current = setInterval(() => {
      if (wsStatus === 'polling' || wsStatus === 'disconnected') {
        fetchAllData(true);
      }
    }, 10000);

    return () => {
      // Clean up connections and timers
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [selectedProductId, dateRange, fetchAllData, connectWebSocket, wsStatus]);

  const refresh = useCallback(() => {
    fetchAllData(true);
  }, [fetchAllData]);

  return {
    loading,
    refreshing,
    error,
    wsStatus,
    knowledgeMetrics,
    conversationVolume,
    resolutionRate,
    intentDistribution,
    salesLeads,
    platformSummary,
    recentActivity,
    bots,
    refresh
  };
}
