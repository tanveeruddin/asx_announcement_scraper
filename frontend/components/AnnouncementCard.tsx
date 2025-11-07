import Link from 'next/link';
import { AnnouncementList } from '@/lib/api';
import { format } from 'date-fns';

interface Props {
  announcement: AnnouncementList;
}

export default function AnnouncementCard({ announcement }: Props) {
  // Format date
  const formattedDate = format(new Date(announcement.announcement_date), 'MMM dd, yyyy HH:mm');

  // Sentiment badge color
  const getSentimentColor = (sentiment: string | null) => {
    if (!sentiment) return 'bg-gray-100 text-gray-700';
    switch (sentiment.toLowerCase()) {
      case 'bullish':
        return 'bg-green-100 text-green-700';
      case 'bearish':
        return 'bg-red-100 text-red-700';
      case 'neutral':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <Link href={`/announcements/${announcement.id}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-lg transition-shadow cursor-pointer">
        {/* Header Row */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            {/* ASX Code & Company */}
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-lg text-blue-600">{announcement.asx_code}</span>
              {announcement.is_price_sensitive && (
                <span className="bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded font-semibold">
                  $ Price Sensitive
                </span>
              )}
            </div>
            {announcement.company && (
              <p className="text-sm text-gray-600">{announcement.company.company_name}</p>
            )}
          </div>

          {/* Sentiment Badge */}
          {announcement.sentiment && (
            <span
              className={`text-xs px-3 py-1 rounded-full font-semibold ${getSentimentColor(
                announcement.sentiment
              )}`}
            >
              {announcement.sentiment.toUpperCase()}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-base font-semibold mb-2 line-clamp-2">{announcement.title}</h3>

        {/* Meta Information */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>📅 {formattedDate}</span>
          {announcement.num_pages && <span>📄 {announcement.num_pages} pages</span>}
          {announcement.file_size_kb && (
            <span>💾 {Math.round(announcement.file_size_kb)} KB</span>
          )}
        </div>

        {/* Status */}
        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
          {announcement.processed_at ? (
            <span className="text-green-600">✓ Analyzed</span>
          ) : announcement.downloaded_at ? (
            <span className="text-blue-600">⏳ Processing</span>
          ) : (
            <span className="text-gray-400">⏳ Pending</span>
          )}
        </div>
      </div>
    </Link>
  );
}
