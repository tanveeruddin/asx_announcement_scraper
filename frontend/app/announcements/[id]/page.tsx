'use client';

import { useState, useEffect } from 'react';
import { use } from 'react';
import Link from 'next/link';
import { getAnnouncement, AnnouncementDetail } from '@/lib/api';
import { format } from 'date-fns';

export default function AnnouncementDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [announcement, setAnnouncement] = useState<AnnouncementDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnnouncement();
  }, [id]);

  async function loadAnnouncement() {
    try {
      setLoading(true);
      setError(null);
      const data = await getAnnouncement(id);
      setAnnouncement(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load announcement');
    } finally {
      setLoading(false);
    }
  }

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
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-blue-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <Link href="/announcements" className="text-xl font-bold hover:text-blue-100">
            ← Back to Announcements
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8 max-w-5xl">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading announcement...</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            <h3 className="font-semibold mb-1">Error</h3>
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && announcement && (
          <div>
            {/* Header Section */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl font-bold text-blue-600">{announcement.asx_code}</h1>
                    {announcement.is_price_sensitive && (
                      <span className="bg-orange-100 text-orange-700 text-sm px-3 py-1 rounded-full font-semibold">
                        $ Price Sensitive
                      </span>
                    )}
                  </div>
                  {announcement.company && (
                    <p className="text-lg text-gray-700 mb-1">{announcement.company.company_name}</p>
                  )}
                  {announcement.company?.industry && (
                    <p className="text-sm text-gray-500">Industry: {announcement.company.industry}</p>
                  )}
                </div>
                {announcement.analysis?.sentiment && (
                  <span
                    className={`text-sm px-4 py-2 rounded-full font-semibold ${getSentimentColor(
                      announcement.analysis.sentiment
                    )}`}
                  >
                    {announcement.analysis.sentiment.toUpperCase()}
                  </span>
                )}
              </div>

              <h2 className="text-xl font-semibold mb-3">{announcement.title}</h2>

              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                <span>
                  📅 {format(new Date(announcement.announcement_date), 'MMMM dd, yyyy HH:mm')}
                </span>
                {announcement.num_pages && <span>📄 {announcement.num_pages} pages</span>}
                {announcement.file_size_kb && (
                  <span>💾 {Math.round(announcement.file_size_kb)} KB</span>
                )}
              </div>

              <div className="mt-4">
                <a
                  href={announcement.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                  View PDF →
                </a>
              </div>
            </div>

            {/* AI Analysis Section */}
            {announcement.analysis && (
              <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
                <h3 className="text-xl font-bold mb-4">🤖 AI Analysis</h3>

                {/* Summary */}
                {announcement.analysis.summary && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Summary</h4>
                    <p className="text-gray-700 leading-relaxed">{announcement.analysis.summary}</p>
                  </div>
                )}

                {/* Key Insights */}
                {announcement.analysis.key_insights && announcement.analysis.key_insights.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Key Insights</h4>
                    <ul className="space-y-2">
                      {announcement.analysis.key_insights.map((insight, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-blue-600 mt-1">•</span>
                          <span className="text-gray-700">{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Analysis Metadata */}
                <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
                  <div className="flex gap-4">
                    {announcement.analysis.llm_model && (
                      <span>Model: {announcement.analysis.llm_model}</span>
                    )}
                    {announcement.analysis.confidence_score && (
                      <span>
                        Confidence: {(announcement.analysis.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                    {announcement.analysis.processing_time_ms && (
                      <span>Processing: {announcement.analysis.processing_time_ms}ms</span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Stock Data Section */}
            {announcement.stock_data && announcement.stock_data.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">📊 Stock Performance</h3>
                {announcement.stock_data.map((stock, index) => (
                  <div key={index}>
                    <div className="grid md:grid-cols-2 gap-4">
                      {/* Current Price */}
                      {stock.price_at_announcement && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">Price at Announcement</div>
                          <div className="text-2xl font-bold text-gray-900">
                            ${stock.price_at_announcement.toFixed(2)}
                          </div>
                        </div>
                      )}

                      {/* Market Cap */}
                      {stock.market_cap && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">Market Cap</div>
                          <div className="text-2xl font-bold text-gray-900">
                            ${(stock.market_cap / 1000000000).toFixed(2)}B
                          </div>
                        </div>
                      )}

                      {/* Performance Metrics */}
                      {stock.performance_1m_pct && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">1M Performance</div>
                          <div
                            className={`text-2xl font-bold ${
                              stock.performance_1m_pct > 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {stock.performance_1m_pct > 0 ? '+' : ''}
                            {stock.performance_1m_pct.toFixed(2)}%
                          </div>
                        </div>
                      )}

                      {stock.performance_3m_pct && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">3M Performance</div>
                          <div
                            className={`text-2xl font-bold ${
                              stock.performance_3m_pct > 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {stock.performance_3m_pct > 0 ? '+' : ''}
                            {stock.performance_3m_pct.toFixed(2)}%
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-gray-600">
          <p>© 2025 ASX Announcements SaaS</p>
        </div>
      </footer>
    </div>
  );
}
