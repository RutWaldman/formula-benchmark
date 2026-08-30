/**
 * ResultsVerifier component for the Dynamic Formula Benchmark Dashboard
 * Shows verification status and displays discrepancies if any methods disagree
 * 
 * Validates: Requirements 7.1
 */

import { useVerification } from '../hooks';
import { METHOD_CONFIGS, type MethodId } from '../types';

/**
 * ResultsVerifier component displays verification status and discrepancies
 * Verifies that all calculation methods produce identical results
 */
export function ResultsVerifier() {
  const { data: verification, isLoading, error, refetch, isFetching } = useVerification();

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="h-24 bg-gray-100 rounded mb-4" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Results Verification</h2>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg
              className="h-5 w-5 text-red-500 mr-2"
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
            <span className="text-red-700 font-medium">Error loading verification results</span>
          </div>
          <p className="text-red-600 text-sm mt-2">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const isValid = verification?.isValid ?? false;
  const discrepancies = verification?.discrepancies ?? [];
  const totalRecords = verification?.totalRecordsChecked ?? 0;
  const methodsCompared = verification?.methodsCompared ?? [];
  const timestamp = verification?.timestamp;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Results Verification</h2>
            <p className="text-sm text-gray-500 mt-1">
              Cross-method result comparison
            </p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className={`p-2 rounded-md transition-colors ${
              isFetching
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
            }`}
            title="Re-verify results"
          >
            <svg
              className={`h-5 w-5 ${isFetching ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Status Summary */}
      <div className="p-6">
        <div
          className={`rounded-lg p-6 ${
            isValid
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center">
            {isValid ? (
              <svg
                className="h-10 w-10 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            ) : (
              <svg
                className="h-10 w-10 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
            <div className="ml-4">
              <h3
                className={`text-xl font-semibold ${
                  isValid ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {isValid ? 'All Results Match' : 'Discrepancies Found'}
              </h3>
              <p className={isValid ? 'text-green-600' : 'text-red-600'}>
                {isValid
                  ? 'All calculation methods produced identical results'
                  : `${discrepancies.length} discrepanc${discrepancies.length === 1 ? 'y' : 'ies'} detected between methods`}
              </p>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center">
              <svg
                className="h-8 w-8 text-indigo-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <div className="ml-3">
                <p className="text-sm text-gray-500">Records Checked</p>
                <p className="text-2xl font-bold text-gray-900">
                  {totalRecords.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center">
              <svg
                className="h-8 w-8 text-purple-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <div className="ml-3">
                <p className="text-sm text-gray-500">Methods Compared</p>
                <p className="text-2xl font-bold text-gray-900">
                  {methodsCompared.length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center">
              <svg
                className={`h-8 w-8 ${discrepancies.length > 0 ? 'text-red-500' : 'text-green-500'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div className="ml-3">
                <p className="text-sm text-gray-500">Discrepancies</p>
                <p className="text-2xl font-bold text-gray-900">
                  {discrepancies.length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Methods Compared */}
        {methodsCompared.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Methods Compared</h4>
            <div className="flex flex-wrap gap-2">
              {methodsCompared.map((method) => {
                const config = METHOD_CONFIGS[method as MethodId];
                return (
                  <span
                    key={method}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                    style={{
                      backgroundColor: config ? `${config.color}20` : '#e5e7eb',
                      color: config?.color || '#374151',
                    }}
                  >
                    <span
                      className="w-2 h-2 rounded-full mr-2"
                      style={{ backgroundColor: config?.color || '#374151' }}
                    />
                    {config?.displayName || method}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Timestamp */}
        {timestamp && (
          <div className="mt-4 text-xs text-gray-500">
            Last verified: {new Date(timestamp).toLocaleString()}
          </div>
        )}
      </div>

      {/* Discrepancies Table */}
      {discrepancies.length > 0 && (
        <div className="border-t border-gray-200">
          <div className="px-6 py-4 bg-red-50">
            <h4 className="text-sm font-semibold text-red-800">
              Discrepancy Details
            </h4>
            <p className="text-xs text-red-600 mt-1">
              The following records have different results across calculation methods
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Data ID
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Formula ID
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Formula
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    <span className="inline-flex items-center">
                      <span
                        className="w-2 h-2 rounded-full mr-1"
                        style={{ backgroundColor: METHOD_CONFIGS.dotnet.color }}
                      />
                      .NET Result
                    </span>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    <span className="inline-flex items-center">
                      <span
                        className="w-2 h-2 rounded-full mr-1"
                        style={{ backgroundColor: METHOD_CONFIGS.python.color }}
                      />
                      Python Result
                    </span>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    <span className="inline-flex items-center">
                      <span
                        className="w-2 h-2 rounded-full mr-1"
                        style={{ backgroundColor: METHOD_CONFIGS.sql.color }}
                      />
                      SQL Result
                    </span>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Max Difference
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {discrepancies.map((discrepancy, index) => (
                  <tr key={`${discrepancy.dataId}-${discrepancy.targilId}-${index}`} className="hover:bg-red-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {discrepancy.dataId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      #{discrepancy.targilId}
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono text-gray-700">
                        {discrepancy.formula}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-gray-900">
                        {discrepancy.dotnetResult !== null
                          ? discrepancy.dotnetResult.toFixed(6)
                          : <span className="text-gray-400">null</span>}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-gray-900">
                        {discrepancy.pythonResult !== null
                          ? discrepancy.pythonResult.toFixed(6)
                          : <span className="text-gray-400">null</span>}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-gray-900">
                        {discrepancy.sqlResult !== null
                          ? discrepancy.sqlResult.toFixed(6)
                          : <span className="text-gray-400">null</span>}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-red-600 font-medium">
                        {discrepancy.maxDifference.toFixed(6)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state for no discrepancies when valid */}
      {isValid && discrepancies.length === 0 && totalRecords > 0 && (
        <div className="border-t border-gray-200 px-6 py-8 text-center">
          <svg
            className="mx-auto h-12 w-12 text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Perfect Match!</h3>
          <p className="mt-1 text-sm text-gray-500">
            All {totalRecords.toLocaleString()} records produced identical results across all methods.
          </p>
        </div>
      )}
    </div>
  );
}

export default ResultsVerifier;
