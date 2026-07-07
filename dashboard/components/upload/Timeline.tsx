import type { PipelineTimelineItem } from '../../types/upload';
import { formatTimestamp } from '../../utils/uploadFormatting';

interface TimelineProps {
  items: PipelineTimelineItem[];
}

export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="upload-timeline">
      {items.map((item) => (
        <li key={item.step} className={`upload-timeline__item upload-timeline__item--${item.state}`}>
          <span />
          <div>
            <strong>{item.label}</strong>
            <small>{item.timestamp ? formatTimestamp(item.timestamp) : 'Pending'}</small>
          </div>
        </li>
      ))}
    </ol>
  );
}
