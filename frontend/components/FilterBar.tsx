interface Props {
  priceSensitiveOnly: boolean;
  onPriceSensitiveChange: (value: boolean) => void;
  sentiment: string;
  onSentimentChange: (value: string) => void;
  onReset: () => void;
}

export default function FilterBar({
  priceSensitiveOnly,
  onPriceSensitiveChange,
  sentiment,
  onSentimentChange,
  onReset,
}: Props) {
  const hasFilters = priceSensitiveOnly || sentiment;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <div className="flex flex-wrap items-center gap-4">
        <h3 className="font-semibold text-gray-700">Filters:</h3>

        {/* Price Sensitive Toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={priceSensitiveOnly}
            onChange={(e) => onPriceSensitiveChange(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded"
          />
          <span className="text-sm">Price Sensitive Only</span>
        </label>

        {/* Sentiment Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-700">Sentiment:</label>
          <select
            value={sentiment}
            onChange={(e) => onSentimentChange(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="bullish">Bullish</option>
            <option value="bearish">Bearish</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>

        {/* Reset Button */}
        {hasFilters && (
          <button
            onClick={onReset}
            className="ml-auto text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Reset Filters
          </button>
        )}
      </div>
    </div>
  );
}
