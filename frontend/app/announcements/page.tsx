'use client';

import { useState, useEffect } from 'react';
import { getAnnouncements, AnnouncementList, PaginatedResponse } from '@/lib/api';
import AnnouncementCard from '@/components/AnnouncementCard';
import FilterBar from '@/components/FilterBar';
import Header from '@/components/Header';

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<PaginatedResponse<AnnouncementList> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [page, setPage] = useState(1);
  const [pricesSensitiveOnly, setPriceSensitiveOnly] = useState(false);
  const [sentiment, setSentiment] = useState<string>('');

  useEffect(() => {
    loadAnnouncements();
  }, [page, priceSensitiveOnly, sentiment]);

  async function loadAnnouncements() {
    try {
      setLoading(true);
      setError(null);
      const data = await getAnnouncements({
        page,
        page_size: 20,
        price_sensitive_only: priceSensitiveOnly,
        sentiment: sentiment || undefined,
      });
      setAnnouncements(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load announcements');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header with authentication */}
      <Header />

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Latest Announcements</h1>
          <p className="text-gray-600">
            Track price-sensitive ASX company announcements with AI-powered insights
          </p>
        </div>

        {/* Filters */}
        <FilterBar
          priceSensitiveOnly={priceSensitiveOnly}
          onPriceSensitiveChange={setPriceSensitiveOnly}
          sentiment={sentiment}
          onSentimentChange={setSentiment}
          onReset={() => {
            setPriceSensitiveOnly(false);
            setSentiment('');
            setPage(1);
          }}
        />

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading announcements...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            <h3 className="font-semibold mb-1">Error Loading Announcements</h3>
            <p>{error}</p>
            <button
              onClick={loadAnnouncements}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Announcements List */}
        {!loading && !error && announcements && (
          <>
            {/* Stats */}
            <div className="mb-4 text-sm text-gray-600">
              Showing {announcements.items.length} of {announcements.metadata.total} announcements
              (Page {announcements.metadata.page} of {announcements.metadata.total_pages})
            </div>

            {/* Cards Grid */}
            {announcements.items.length > 0 ? (
              <div className="grid gap-4 mb-8">
                {announcements.items.map((announcement) => (
                  <AnnouncementCard key={announcement.id} announcement={announcement} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-lg">
                <p className="text-gray-600 text-lg">No announcements found</p>
                <p className="text-gray-500 mt-2">Try adjusting your filters</p>
              </div>
            )}

            {/* Pagination */}
            {announcements.metadata.total_pages > 1 && (
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                <span className="px-4 py-2 bg-white border border-gray-300 rounded-lg">
                  Page {page} of {announcements.metadata.total_pages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === announcements.metadata.total_pages}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
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
