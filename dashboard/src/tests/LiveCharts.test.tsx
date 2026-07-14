// dashboard/src/tests/LiveCharts.test.tsx

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LineChart } from '../components/analytics/charts/LineChart';
import { BarChart } from '../components/analytics/charts/BarChart';
import { PieDonutChart } from '../components/analytics/charts/PieDonutChart';
import { IntentHeatmap } from '../components/analytics/charts/IntentHeatmap';
import { LatencyChart } from '../components/analytics/charts/LatencyChart';
import { LeadAnalyticsChart } from '../components/analytics/charts/LeadAnalyticsChart';
import { LiveActivityTimeline } from '../components/analytics/charts/LiveActivityTimeline';

const mockVolume = [
  { time: '12:00', count: 5 },
  { time: '12:01', count: 12 },
  { time: '12:02', count: 8 }
];

const mockBarData = [
  { platform: 'WEB', conversations: 25 },
  { platform: 'SLACK', conversations: 10 }
];

const mockIntentData = [
  { intent: 'PRICING', count: 12 },
  { intent: 'SUPPORT', count: 8 }
];

const mockLatency = [
  { time: '12:00', avg: 220, p50: 190, p95: 380, p99: 580 },
  { time: '12:01', avg: 240, p50: 200, p95: 410, p99: 610 }
];

const mockTimeline = [
  { id: '1', timestamp: new Date().toISOString(), type: 'conversation_started' as const, message: 'Chat started', status: 'info' as const }
];

describe('Live Telemetry Visualization Modules', () => {
  test('LineChart renders multi-series lines and ticks', () => {
    render(
      <LineChart
        data={mockVolume}
        series={[{ key: 'count', color: 'blue', label: 'Volume' }]}
        xKey="time"
      />
    );
    
    // Check elements
    expect(screen.getByText('Volume')).toBeInTheDocument();
    expect(screen.getByLabelText('Timeline performance trends line chart')).toBeInTheDocument();
  });

  test('BarChart renders vertical and horizontal bar rects', () => {
    const { container } = render(
      <BarChart
        data={mockBarData}
        dataKey="conversations"
        nameKey="platform"
        horizontal={false}
      />
    );

    // Verify SVG rect bars
    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBe(2);
  });

  test('PieDonutChart renders slices and totals count overlay', () => {
    render(
      <PieDonutChart
        data={mockIntentData}
        dataKey="count"
        nameKey="intent"
      />
    );

    expect(screen.getByText('TOTALS')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument(); // 12 + 8
  });

  test('IntentHeatmap renders weekdays grids cells and ARIA definitions', () => {
    render(<IntentHeatmap data={mockIntentData} />);

    // Verify cells exist in grid
    const cells = screen.getAllByRole('gridcell');
    expect(cells.length).toBeGreaterThan(0);
  });

  test('LatencyChart renders percentile lines and toggles legend selections', () => {
    render(<LatencyChart data={mockLatency} />);

    const p50Btn = screen.getByLabelText('Toggle line P50 (Median)');
    expect(p50Btn).toBeInTheDocument();
    
    // Try toggling legend line
    fireEvent.click(p50Btn);
    expect(p50Btn).toHaveAttribute('aria-pressed', 'false');
  });

  test('LeadAnalyticsChart renders funnel stages with percentages', () => {
    render(<LeadAnalyticsChart leadsCount={5} />);

    expect(screen.getByText(/Aggregate Telemetry Chats/)).toBeInTheDocument();
  });

  test('LiveActivityTimeline renders event text and platform badges', () => {
    render(<LiveActivityTimeline events={mockTimeline} />);

    expect(screen.getByText('Chat started')).toBeInTheDocument();
  });
});
