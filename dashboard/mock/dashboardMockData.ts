// Mock data provider for Envoy AI Admin Dashboard scaffolding

export interface KPIMetric {
  id: string;
  title: string;
  value: string | number;
  trend: number; // positive = up, negative = down, 0 = neutral
  trendLabel: string;
  tooltip: string;
}

export interface SalesLead {
  id: string;
  name: string;
  score: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  intent: string;
  status: 'new' | 'contacted' | 'qualified' | 'disqualified';
  platform: string;
  timestamp: string;
}

export interface ConversationFeedItem {
  id: string;
  avatar: string;
  title: string;
  intentBadge: string;
  timestamp: string;
  status: 'active' | 'resolved' | 'escalated';
}

export interface KnowledgeMetrics {
  indexedDocuments: number;
  vectorCount: number;
  storageUsed: string;
  embeddingStatus: 'synced' | 'indexing' | 'failed';
}

export interface PlatformHealthItem {
  name: string;
  status: 'healthy' | 'warning' | 'offline';
  latency: string;
  uptime: string;
}

export interface ChartSeriesPoint {
  label: string;
  value: number;
  secondaryValue?: number;
}

export const mockKPIMetrics: KPIMetric[] = [
  {
    id: 'total-conversations',
    title: 'Total Conversations',
    value: '24,871',
    trend: 12.4,
    trendLabel: 'vs last week',
    tooltip: 'Total volume of user interactions across all channels this month.'
  },
  {
    id: 'active-platforms',
    title: 'Active Platforms',
    value: '8 / 8',
    trend: 0,
    trendLabel: 'All channels operational',
    tooltip: 'Number of connected message distribution channels that are currently active.'
  },
  {
    id: 'documents-indexed',
    title: 'Documents Indexed',
    value: '128',
    trend: 4.8,
    trendLabel: '12 added recently',
    tooltip: 'Total processed business documents loaded into the semantic search engine.'
  },
  {
    id: 'knowledge-chunks',
    title: 'Knowledge Chunks',
    value: '9,243',
    trend: 8.2,
    trendLabel: 'Vector representations sync\'d',
    tooltip: 'Granular context snippets parsed from documents and registered in Qdrant.'
  },
  {
    id: 'resolution-rate',
    title: 'Resolution Rate',
    value: '94.2%',
    trend: 1.5,
    trendLabel: 'vs historical average',
    tooltip: 'Percentage of conversations successfully closed without operator handoff.'
  },
  {
    id: 'avg-response-time',
    title: 'Avg Response Time',
    value: '1.8s',
    trend: -10.5, // negative is good for response times (speedup)
    trendLabel: 'decrease (faster)',
    tooltip: 'Average AI model generation and streaming delivery latency.'
  },
  {
    id: 'sales-leads',
    title: 'Sales Leads',
    value: '37',
    trend: 18.2,
    trendLabel: 'vs last week',
    tooltip: 'Conversations classified with high purchase intent forwarded to CRMs.'
  },
  {
    id: 'active-sessions',
    title: 'Active Sessions',
    value: '142',
    trend: 25.0,
    trendLabel: 'real-time users',
    tooltip: 'Number of concurrent active chat connections currently open.'
  }
];

export const mockSalesLeads: SalesLead[] = [
  {
    id: 'L-001',
    name: 'Sarah Connor',
    score: 95,
    priority: 'critical',
    intent: 'Enterprise Licensing Inquiry',
    status: 'new',
    platform: 'web-chat',
    timestamp: '2 mins ago'
  },
  {
    id: 'L-002',
    name: 'Bruce Wayne',
    score: 88,
    priority: 'high',
    intent: 'Security & Compliance Review',
    status: 'contacted',
    platform: 'slack-bot',
    timestamp: '15 mins ago'
  },
  {
    id: 'L-003',
    name: 'Tony Stark',
    score: 92,
    priority: 'critical',
    intent: 'Custom API Scale Plan',
    status: 'new',
    platform: 'web-chat',
    timestamp: '1 hour ago'
  },
  {
    id: 'L-004',
    name: 'Clark Kent',
    score: 74,
    priority: 'medium',
    intent: 'Multi-tenant Setup Demo',
    status: 'qualified',
    platform: 'discord',
    timestamp: '3 hours ago'
  },
  {
    id: 'L-005',
    name: 'Diana Prince',
    score: 61,
    priority: 'low',
    intent: 'Standard Pricing FAQ',
    status: 'disqualified',
    platform: 'telegram',
    timestamp: '1 day ago'
  }
];

export const mockConversations: ConversationFeedItem[] = [
  {
    id: 'C-8931',
    avatar: 'SC',
    title: 'Sarah Connor',
    intentBadge: 'Enterprise License',
    timestamp: '2 mins ago',
    status: 'active'
  },
  {
    id: 'C-8930',
    avatar: 'BW',
    title: 'Bruce Wayne',
    intentBadge: 'Security Review',
    timestamp: '15 mins ago',
    status: 'active'
  },
  {
    id: 'C-8929',
    avatar: 'TS',
    title: 'Tony Stark',
    intentBadge: 'API Integration',
    timestamp: '1 hour ago',
    status: 'active'
  },
  {
    id: 'C-8928',
    avatar: 'CK',
    title: 'Clark Kent',
    intentBadge: 'Demo Request',
    timestamp: '3 hours ago',
    status: 'resolved'
  },
  {
    id: 'C-8927',
    avatar: 'DP',
    title: 'Diana Prince',
    intentBadge: 'Pricing Question',
    timestamp: '1 day ago',
    status: 'resolved'
  },
  {
    id: 'C-8926',
    avatar: 'PP',
    title: 'Peter Parker',
    intentBadge: 'System Error',
    timestamp: '2 days ago',
    status: 'escalated'
  }
];

export const mockKnowledgeMetrics: KnowledgeMetrics = {
  indexedDocuments: 128,
  vectorCount: 9243,
  storageUsed: '234.5 MB',
  embeddingStatus: 'synced'
};

export const mockPlatformHealth: PlatformHealthItem[] = [
  { name: 'Web Chat Integrator', status: 'healthy', latency: '45ms', uptime: '99.98%' },
  { name: 'Slack Connector', status: 'healthy', latency: '120ms', uptime: '99.95%' },
  { name: 'Discord Webhook Hub', status: 'healthy', latency: '85ms', uptime: '99.90%' },
  { name: 'Telegram Gateway', status: 'warning', latency: '350ms', uptime: '98.54%' },
  { name: 'MS Teams Sync Service', status: 'offline', latency: '—', uptime: '82.11%' },
  { name: 'Qdrant Vector DB', status: 'healthy', latency: '12ms', uptime: '99.99%' },
  { name: 'PostgreSQL Core DB', status: 'healthy', latency: '4ms', uptime: '100.00%' },
  { name: 'LLM Gateway API', status: 'healthy', latency: '180ms', uptime: '99.92%' }
];

export const mockLineChartData: ChartSeriesPoint[] = [
  { label: '09:00', value: 120 },
  { label: '10:00', value: 150 },
  { label: '11:00', value: 240 },
  { label: '12:00', value: 190 },
  { label: '13:00', value: 210 },
  { label: '14:00', value: 280 },
  { label: '15:00', value: 310 },
  { label: '16:00', value: 290 },
  { label: '17:00', value: 350 }
];

export const mockAreaChartData: ChartSeriesPoint[] = [
  { label: 'Mon', value: 1200, secondaryValue: 1000 },
  { label: 'Tue', value: 1350, secondaryValue: 1100 },
  { label: 'Wed', value: 1500, secondaryValue: 1250 },
  { label: 'Thu', value: 1400, secondaryValue: 1150 },
  { label: 'Fri', value: 1750, secondaryValue: 1400 },
  { label: 'Sat', value: 900, secondaryValue: 700 },
  { label: 'Sun', value: 950, secondaryValue: 750 }
];

export const mockBarChartData: ChartSeriesPoint[] = [
  { label: 'Web Chat', value: 4500 },
  { label: 'Slack', value: 2800 },
  { label: 'Discord', value: 1900 },
  { label: 'Telegram', value: 1200 },
  { label: 'MS Teams', value: 400 },
  { label: 'API Keys', value: 800 }
];

export const mockPieChartData: ChartSeriesPoint[] = [
  { label: 'Enterprise Pricing Intent', value: 45 },
  { label: 'Support / Tech Help', value: 25 },
  { label: 'Sales / Product Inquiry', value: 18 },
  { label: 'Out of Scope / Noise', value: 12 }
];

export const mockHeatmapData = {
  xLabels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  yLabels: ['Morning', 'Afternoon', 'Evening', 'Night'],
  values: [
    [10, 15, 20, 18, 22, 5, 4], // Morning
    [25, 30, 42, 38, 40, 12, 10], // Afternoon
    [32, 35, 48, 45, 52, 14, 12], // Evening
    [8, 12, 15, 14, 18, 6, 5] // Night
  ]
};

export const mockTimelineEvents = [
  { time: '16:22', text: 'Sarah Connor conversation escalated to High priority', type: 'warning' },
  { time: '16:15', text: 'Admissions Portal Knowledge Base synchronized successfully', type: 'success' },
  { time: '16:04', text: 'Telegram Gateway reports high latency (350ms)', type: 'warning' },
  { time: '15:58', text: 'Bruce Wayne qualified as enterprise CRM sales lead', type: 'success' },
  { time: '15:30', text: 'API Key rotation executed for Tensor Product Client', type: 'info' },
  { time: '14:45', text: 'MS Teams Sync Service status changed to OFFLINE', type: 'danger' }
];

export const mockActivityStream = [
  { id: '1', user: 'AI Assistant', action: 'answered inquiry', subject: ' Sarah Connor (Web Chat)', time: 'Just now' },
  { id: '2', user: 'System', action: 'indexed document', subject: 'compliance_audit_2026.pdf', time: '5 mins ago' },
  { id: '3', user: 'AI Assistant', action: 'captured lead', subject: 'Bruce Wayne (Slack)', time: '12 mins ago' },
  { id: '4', user: 'Ops Admin', action: 'updated setting', subject: 'Qdrant search distance metric', time: '30 mins ago' },
  { id: '5', user: 'System', action: 'vectorized chunks', subject: '243 chunks from hr_handbook.md', time: '1 hour ago' }
];
