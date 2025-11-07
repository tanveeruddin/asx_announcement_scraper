import Link from "next/link";
import Header from "@/components/Header";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header with authentication */}
      <Header />

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              Stay Ahead of the Market
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Real-time tracking of ASX price-sensitive announcements with AI-powered analysis
            </p>
            <Link
              href="/announcements"
              className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              View Announcements
            </Link>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
              <div className="text-3xl mb-3">🔍</div>
              <h3 className="text-xl font-semibold mb-2">Real-Time Tracking</h3>
              <p className="text-gray-600">
                Automatic scraping of ASX announcements every hour during market hours
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
              <div className="text-3xl mb-3">🤖</div>
              <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
              <p className="text-gray-600">
                Gemini-powered sentiment analysis and key insights extraction
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
              <div className="text-3xl mb-3">📊</div>
              <h3 className="text-xl font-semibold mb-2">Market Data</h3>
              <p className="text-gray-600">
                Stock prices, market cap, and historical performance metrics
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-8 rounded-lg border border-blue-200">
            <h3 className="text-2xl font-bold mb-4">Platform Status</h3>
            <div className="grid md:grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold text-blue-600">285+</div>
                <div className="text-gray-600">Announcements Tracked</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-600">76+</div>
                <div className="text-gray-600">Price-Sensitive</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-600">100%</div>
                <div className="text-gray-600">API Uptime</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-gray-600">
          <p>© 2025 ASX Announcements SaaS. Built with Next.js, FastAPI & Google Gemini.</p>
        </div>
      </footer>
    </div>
  );
}
