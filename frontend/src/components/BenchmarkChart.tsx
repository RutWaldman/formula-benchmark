/**
 * Benchmark Chart Component
 * Displays execution time comparison per formula using Recharts bar/line charts
 * 
 * Validates: Requirements 6.3
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { useBenchmarkResults } from '../hooks';
import { METHOD_CONFIGS, type BenchmarkResult, type ChartDataPoint } from '../types';

/**
 * Transform benchmark results into chart-compatible data format
 */
function transformToChartData(results: BenchmarkResult[]): ChartDataPoint[] {
  return results.map((result) => ({
    name: `Formula ${result.targilId}`,
    formula: result.formula,
    dotnet: result.dotnetTime,
    python: result.pythonTime,
    sql: result.sqlTime,
  }));
}

/**
 * Custom tooltip component for the chart
 */
function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const formulaData = payload[0]?.payload as ChartDataPoint | undefined;

  return (
    <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
      <p className="font-semibold text-gray-900 mb-1">{label}</p>
      {formulaData?.formula && (
        <p className="text-xs text-gray-500 mb-2 font-mono bg-gray-50 px-2 py-1 rounded">
          {formulaData.formula}
        </p>
      )}
      <div className="space-y-1">
        {payload.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-gray-700">{entry.name}</span>
            </div>
            <span className="text-sm font-medium text-gray-900">
              {entry.value !== null && entry.value !== undefined
                ? `${entry.value.toFixed(4)}s`
                : 'N/A'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Loading skeleton component
 */
function ChartSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-48 mb-4" />
      <div className="h-80 bg-gray-100 rounded-lg flex items-end justify-around p-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="flex gap-1 items-end">
            <div
              className="w-4 bg-gray-300 rounded-t"
              style={{ height: `${Math.random() * 150 + 50}px` }}
            />
            <div
              className="w-4 bg-gray-200 rounded-t"
              style={{ height: `${Math.random() * 150 + 50}px` }}
            />
            <div
              className="w-4 bg-gray-300 rounded-t"
              style={{ height: `${Math.random() * 150 + 50}px` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Error display component
 */
function ChartError({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-80 bg-red-50 rounded-lg border border-red-200">
      <svg
        className="h-12 w-12 text-red-400 mb-3"
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
      <p className="text-red-600 font-medium">Failed to load benchmark data</p>
      <p className="text-red-500 text-sm mt-1">{message}</p>
    </div>
  );
}

/**
 * Empty state component
 */
function ChartEmpty() {
  return (
    <div className="flex flex-col items-center justify-center h-80 bg-gray-50 rounded-lg border border-gray-200">
      <svg
        className="h-12 w-12 text-gray-400 mb-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <p className="text-gray-600 font-medium">No benchmark data available</p>
      <p className="text-gray-500 text-sm mt-1">Run a benchmark to see results</p>
    </div>
  );
}

/**
 * BenchmarkChart component
 * Displays a bar chart comparing execution times across different calculation methods
 */
export function BenchmarkChart() {
  const { data: results, isLoading, error } = useBenchmarkResults();

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <ChartSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Execution Time by Formula
        </h3>
        <ChartError message={error.message} />
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Execution Time by Formula
        </h3>
        <ChartEmpty />
      </div>
    );
  }

  const chartData = transformToChartData(results);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Execution Time by Formula
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Performance comparison across {results.length} formulas
          </p>
        </div>
        <div className="flex items-center gap-4">
          {Object.values(METHOD_CONFIGS).map((config) => (
            <div key={config.id} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: config.color }}
              />
              <span className="text-xs text-gray-600">{config.displayName}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 20, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
              label={{
                value: 'Time (seconds)',
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: 12, fill: '#6B7280' },
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: 20 }}
              formatter={(value) => (
                <span className="text-sm text-gray-700">{value}</span>
              )}
            />
            <Bar
              dataKey="dotnet"
              name={METHOD_CONFIGS.dotnet.displayName}
              fill={METHOD_CONFIGS.dotnet.color}
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="python"
              name={METHOD_CONFIGS.python.displayName}
              fill={METHOD_CONFIGS.python.color}
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="sql"
              name={METHOD_CONFIGS.sql.displayName}
              fill={METHOD_CONFIGS.sql.color}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default BenchmarkChart;
