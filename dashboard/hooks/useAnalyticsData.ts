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

export interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'conversation_started' | 'conversation_completed' | 'lead_detected' | 'error' | 'document_updated' | 'platform_event';
  message: string;
  status: 'info' | 'success' | 'warning' | 'error';
  platform?: string;
}

export interface LatencyDataPoint {
  time: string;
  avg: number;
  p50: number;
  p95: number;
  p99: number;
}

export interface VolumeDataPoint {
  time: string;
  count: number;
}

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
  timelineEvents: TimelineEvent[];
  liveLatencyPoints: LatencyDataPoint[];
  liveVolumePoints: VolumeDataPoint[];
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

  // Sliding telemetry states
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [liveLatencyPoints, setLiveLatencyPoints] = useState<LatencyDataPoint[]>([]);
  const [liveVolumePoints, setLiveVolumePoints] = useState<VolumeDataPoint[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const simulationIntervalRef = useRef<NodeJS.Timeout | null>(null);
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
          const prods = await prodRes.json();
          const found = prods.find((p: any) => p.product_id === selectedProductId);
          if (found) {
            selectedProductUuid = found.id;
            activeProductUuidRef.current = found.id;
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

        const isHeaderFiltered = !!headers['X-Envoy-API-Key'];

        if (selectedProductId && !isHeaderFiltered) {
          const tenantBotIds = bots
            .filter((b) => b.product_id === selectedProductId)
            .map((b) => b.id);

          const filteredLeads = leadsRes.leads.filter(
            (lead) => lead.bot_id && tenantBotIds.includes(lead.bot_id)
          );

          const filteredPlatform = pSummary.filter(
            (p) => p.bot_id && tenantBotIds.includes(p.bot_id)
          );

          setConversationVolume(volume);
          setResolutionRate(resRate);
          setIntentDistribution(intends);
          setSalesLeads(filteredLeads);
          setPlatformSummary(filteredPlatform);
        } else {
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
    if (!selectedProductId) {
      setWsStatus('polling');
      return;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setWsStatus('connecting');

    let token = localStorage.getItem(`token_${selectedProductId}`);
    if (!token) {
      token = 'ws_token_a';
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

        // Push connection success to timeline
        setTimelineEvents((prev) => [
          {
            id: `sys-${Date.now()}`,
            timestamp: new Date().toISOString(),
            type: 'platform_event',
            message: `Telemetry connection established for tenant ${selectedProductId}`,
            status: 'success'
          },
          ...prev.slice(0, 14)
        ]);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'analytics_update' && payload.data) {
            console.log('Real-Time WebSocket Analytics Update Received:', payload);
            const data = payload.data;
            
            if (data.conversation_volume) setConversationVolume(data.conversation_volume);
            if (data.resolution_rate) setResolutionRate(data.resolution_rate);
            if (data.intent_distribution) setIntentDistribution(data.intent_distribution);
            if (data.sales_leads) setSalesLeads(data.sales_leads.leads || []);
            if (data.platform_summary) setPlatformSummary(data.platform_summary);

            // Log event to timeline
            setTimelineEvents((prev) => [
              {
                id: `ws-${Date.now()}`,
                timestamp: new Date().toISOString(),
                type: 'platform_event',
                message: `Aggregated analytics metrics synchronized from broadcast channel`,
                status: 'info'
              },
              ...prev.slice(0, 14)
            ]);
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

        if (ev.code === 4003) {
          setWsStatus('polling');
        } else {
          setWsStatus('disconnected');
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 5000);
        }

        // Log close event
        setTimelineEvents((prev) => [
          {
            id: `sys-close-${Date.now()}`,
            timestamp: new Date().toISOString(),
            type: 'platform_event',
            message: `WebSocket channel closed. Activating HTTP polling backup (Code: ${ev.code})`,
            status: 'warning'
          },
          ...prev.slice(0, 14)
        ]);
      };
    } catch (err) {
      console.error('Failed to instantiate WebSocket:', err);
      setWsStatus('polling');
    }
  }, [selectedProductId]);

  // Seed baseline streaming values for line/latency charts on filters reset
  useEffect(() => {
    const now = new Date();
    const seedVolume: VolumeDataPoint[] = [];
    const seedLatency: LatencyDataPoint[] = [];
    
    for (let i = 9; i >= 0; i--) {
      const d = new Date(now.getTime() - i * 60000);
      const timeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
      
      seedVolume.push({
        time: timeStr,
        count: Math.floor(Math.random() * 8) + 3
      });

      const baseLat = Math.floor(Math.random() * 80) + 180;
      seedLatency.push({
        time: timeStr,
        avg: baseLat,
        p50: baseLat - 25,
        p95: baseLat + Math.floor(Math.random() * 120) + 80,
        p99: baseLat + Math.floor(Math.random() * 250) + 200
      });
    }

    setLiveVolumePoints(seedVolume);
    setLiveLatencyPoints(seedLatency);

    setTimelineEvents([
      { id: '1', timestamp: new Date(now.getTime() - 120000).toISOString(), type: 'conversation_started', message: 'New user conversation initiated on platform web', status: 'info', platform: 'web' },
      { id: '2', timestamp: new Date(now.getTime() - 90000).toISOString(), type: 'document_updated', message: 'Knowledge database updated: vector synchronization complete for api_docs.pdf', status: 'success' },
      { id: '3', timestamp: new Date(now.getTime() - 60000).toISOString(), type: 'lead_detected', message: 'Sales lead qualified: Pricing inquiry triggered in session sess_9f82', status: 'success', platform: 'slack' },
      { id: '4', timestamp: new Date(now.getTime() - 30000).toISOString(), type: 'conversation_completed', message: 'User query resolved on platform teams: FAQ classification standard match', status: 'success', platform: 'teams' }
    ]);
  }, [selectedProductId]);

  // Streaming simulation effect (updates values/charts dynamically every 4.5 seconds to display animations)
  useEffect(() => {
    if (simulationIntervalRef.current) {
      clearInterval(simulationIntervalRef.current);
    }

    simulationIntervalRef.current = setInterval(() => {
      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

      // 1. Streaming conversation count
      const currentCount = Math.floor(Math.random() * 12) + 2;
      setLiveVolumePoints((prev) => {
        const next = [...prev, { time: timeStr, count: currentCount }];
        return next.slice(-12); // Maintain last 12 points
      });

      // 2. Latency percentiles
      const baseLat = Math.floor(Math.random() * 60) + 190;
      setLiveLatencyPoints((prev) => {
        const next = [...prev, {
          time: timeStr,
          avg: baseLat,
          p50: baseLat - Math.floor(Math.random() * 15) - 5,
          p95: baseLat + Math.floor(Math.random() * 100) + 70,
          p99: baseLat + Math.floor(Math.random() * 320) + 220
        }];
        return next.slice(-12);
      });

      // 3. Activity timelines logs
      const eventTypes = [
        { type: 'conversation_started', message: 'New user conversation initiated on platform ', status: 'info', weight: 0.4 },
        { type: 'conversation_completed', message: 'Conversation completed: session resolved on ', status: 'success', weight: 0.3 },
        { type: 'lead_detected', message: 'Sales lead detected: High confidence intent flagged in session ', status: 'success', weight: 0.15 },
        { type: 'error', message: 'API response failure: latency threshold exceeded on LLM gateway', status: 'error', weight: 0.05 },
        { type: 'document_updated', message: 'Knowledge chunk vectorized: chunk_id #vector_8a2d synchronization complete', status: 'success', weight: 0.1 }
      ];

      // Select random item based on weight
      const rand = Math.random();
      let selected = eventTypes[0];
      let sum = 0;
      for (const e of eventTypes) {
        sum += e.weight;
        if (rand <= sum) {
          selected = e;
          break;
        }
      }

      const platforms = ['web', 'slack', 'teams'];
      const randPlatform = platforms[Math.floor(Math.random() * platforms.length)];
      const idStr = Math.floor(Math.random() * 9000 + 1000).toString(16);

      let msg = selected.message;
      if (selected.type === 'conversation_started' || selected.type === 'conversation_completed') {
        msg = `${selected.message}${randPlatform} (Session: sess_${idStr})`;
      } else if (selected.type === 'lead_detected') {
        msg = `${selected.message}sess_${idStr}`;
      }

      setTimelineEvents((prev) => [
        {
          id: `sim-${Date.now()}`,
          timestamp: now.toISOString(),
          type: selected.type as any,
          message: msg,
          status: selected.status as any,
          platform: randPlatform
        },
        ...prev.slice(0, 14)
      ]);
    }, 4500);

    return () => {
      if (simulationIntervalRef.current) {
        clearInterval(simulationIntervalRef.current);
      }
    };
  }, []);

  // Handle active data fetching lifecycle
  useEffect(() => {
    fetchAllData();
    connectWebSocket();

    pollingIntervalRef.current = setInterval(() => {
      if (wsStatus === 'polling' || wsStatus === 'disconnected') {
        fetchAllData(true);
      }
    }, 10000);

    return () => {
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
    timelineEvents,
    liveLatencyPoints,
    liveVolumePoints,
    refresh
  };
}
