/**
 * Comparison Table Component
 * Displays summary statistics for each calculation method with comparison highlighting
 * 
 * Validates: Requirements 6.3
 */

import { useComparison } from '../hooks';
import { METHOD_CONFIGS, type MethodComparison } from '../types';

/**
 * Format time value for display
 */
function formatTime(seconds: number): string {
  if (seconds < 0.001) {
    return `${(seconds * 1000000).toFixed(2)}µs`;
  }
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(2)}ms`;
  }
  return `${seconds.toFixed(4)}s`;
}

/**
 * Loading skeleton component for the table
 */
function TableSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-6 bg-gray-200 rounded w-48 mb-4" />
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              {['Method', 'Total Time', 'Avg Time', 'Min Time', 'Max Time', 'Formulas'].map(
                (header) => (
                  <th key={header} className="px-6 py-3">
                    <div className="h-4 bg-gray-300 rounded w-20" />
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3].map((row) => (
              <tr key={row} className="border-t border-gray-200">
                {[1, 2, 3, 4, 5, 6].map((col) => (
                  <td key={col} className="px-6 py-4">
                    <div className="h-4 bg-gray-200 rounded w-16" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Error display component
 */
function TableError({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 bg-red-50 rounded-lg border border-red-200">
      <svg
        className="h-10 w-10 text-red-400 mb-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p className="text-red-600 font-medium">Failed to load comparison data</p>
      <p className="text-red-500 text-sm mt-1">{message}</p>
    </div>
  );
}

/**
 * Empty state component
 */
function TableEmpty() {
  return (
    <div className="flex flex-col items-center justify-center py-12 bg-gray-50 rounded-lg border border-gray-200">
      <svg
        className="h-10 w-10 text-gray-400 mb-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
        />
      </svg>
      <p className="text-gray-600 font-medium">No comparison data available</p>
      <p className="text-gray-500 text-sm mt-1">Run benchmarks to see method comparison</p>
    </div>
  );
}

/**
 * Get min and max times from comparison data for highlighting
 */
interface ComparisonStats {
  minTotalTime: number;
  maxTotalTime: number;
  minAvgTime: number;
  maxAvgTime: number;
}

function getComparisonStats(data: MethodComparison[]): ComparisonStats {
  const totalTimes = data.map((d) => d.totalTime).filter((t) => t > 0);
  const avgTimes = data.map((d) => d.averageTime).filter((t) => t > 0);

  return {
    minTotalTime: Math.min(...totalTimes),
    maxTotalTime: Math.max(...totalTimes),
    minAvgTime: Math.min(...avgTimes),
    maxAvgTime: Math.max(...avgTimes),
  };
}

/**
 * Get highlight class based on whether this is the fastest/slowest
 */
function getHighlightClass(
  value: number,
  minValue: number,
  maxValue: number
): string {
  if (value === minValue) {
    return 'bg-green-50 text-green-700 font-semibold';
  }
  if (value === maxValue) {
    return 'bg-red-50 text-red-700';
  }
  return '';
}

/**
 * Map API method names to config keys
 */
const METHOD_NAME_MAP: Record<string, keyof typeof METHOD_CONFIGS> = {
  'DotNet_DataTable': 'dotnet',
  'Python_Eval': 'python',
  'SQL_Dynamic': 'sql',
};

/**
 * Method badge component with color
 */
function MethodBadge({ method }: { method: MethodComparison }) {
  // Map API method name to config key
  const configKey = METHOD_NAME_MAP[method.method] || method.method as keyof typeof METHOD_CONFIGS;
  const config = METHOD_CONFIGS[configKey];
  const color = config?.color || method.color || '#6B7280';
  const displayName = config?.displayName || method.method;

  return (
    <div className="flex items-center gap-3">
      <div
        className="w-3 h-3 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
      />
      <div>
        <span className="font-medium text-gray-900">{displayName}</span>
        {config?.description && (
          <p className="text-xs text-gray-500 mt-0.5">{config.description}</p>
        )}
      </div>
    </div>
  );
}

/**
 * ComparisonTable component
 * Displays a table comparing performance statistics across calculation methods
 */
export function ComparisonTable() {
  const { data: comparison, isLoading, error } = useComparison();

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <TableSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Method Comparison
        </h3>
        <TableError message={error.message} />
      </div>
    );
  }

  if (!comparison || comparison.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Method Comparison
        </h3>
        <TableEmpty />
      </div>
    );
  }

  const stats = getComparisonStats(comparison);
  const fastestMethod = comparison.find((c) => c.totalTime === stats.minTotalTime);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Method Comparison</h3>
          <p className="text-sm text-gray-500 mt-1">
            Summary statistics for each calculation method
          </p>
        </div>
        {fastestMethod && (
          <div className="flex items-center gap-2 bg-green-50 px-3 py-1.5 rounded-full">
            <svg
              className="h-4 w-4 text-green-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm font-medium text-green-700">
              Fastest: {fastestMethod.displayName}
            </span>
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr className="bg-gray-50">
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider"
              >
                Method
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider"
              >
                Total Time
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider"
              >
                Avg Time
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider"
              >
                Formulas Processed
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {comparison.map((method) => {
              const totalHighlight = getHighlightClass(
                method.totalTime,
                stats.minTotalTime,
                stats.maxTotalTime
              );
              const avgHighlight = getHighlightClass(
                method.averageTime,
                stats.minAvgTime,
                stats.maxAvgTime
              );

              return (
                <tr
                  key={method.method}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <MethodBadge method={method} />
                  </td>
                  <td
                    className={`px-6 py-4 whitespace-nowrap text-right text-sm ${totalHighlight}`}
                  >
                    {method.totalTime > 0 ? formatTime(method.totalTime) : 'N/A'}
                  </td>
                  <td
                    className={`px-6 py-4 whitespace-nowrap text-right text-sm ${avgHighlight}`}
                  >
                    {method.averageTime > 0 ? formatTime(method.averageTime) : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {method.formulasProcessed}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-6 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-50 border border-green-200" />
          <span>Fastest (best)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-50 border border-red-200" />
          <span>Slowest</span>
        </div>
      </div>
    </div>
  );
}

export default ComparisonTable;
