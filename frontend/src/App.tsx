/**
 * Main application component for the Dynamic Formula Benchmark Dashboard
 * Provides the layout structure with Header, Sidebar, and content area
 * 
 * Validates: Requirements 6.1, 6.2
 */

import { useState } from 'react';
import { Header, Sidebar, BenchmarkChart, ComparisonTable, FormulaList, ResultsVerifier } from './components';
import { useBenchmarkResults } from './hooks/useBenchmark';

/**
 * Navigation section type
 */
type NavigationSection = 'dashboard' | 'formulas' | 'verification' | 'benchmark';

/**
 * Placeholder content for each section
 * These will be replaced with actual components in future tasks
 */
function DashboardContent() {
  const { data: benchmarkResults, isLoading, error } = useBenchmarkResults();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading benchmark data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">Error loading data: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Summary cards */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Records</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">1,000,000</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Formulas</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">{benchmarkResults?.length || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Methods</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">3</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Status</h3>
          <p className="mt-2 text-lg font-bold text-green-600">Ready</p>
        </div>
      </div>
      
      {/* Benchmark Chart - loads its own data */}
      <BenchmarkChart />
      
      {/* Comparison Table - loads its own data */}
      <ComparisonTable />
    </div>
  );
}

function FormulasContent() {
  return <FormulaList />;
}

function VerificationContent() {
  return <ResultsVerifier />;
}

function BenchmarkContent() {
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, { status: string; time?: number; error?: string }>>({});

  const runBenchmark = async (method: 'dotnet' | 'python' | 'sql' | 'all') => {
    setRunning(method);
    setResults(prev => ({ ...prev, [method]: { status: 'running' } }));

    try {
      const response = await fetch(`http://localhost:8000/api/benchmark/execute/${method}`, {
        method: 'POST',
      });
      const data = await response.json();
      
      if (response.ok) {
        setResults(prev => ({ ...prev, [method]: { status: 'success', time: data.totalTime } }));
      } else {
        setResults(prev => ({ ...prev, [method]: { status: 'error', error: data.detail || 'Failed' } }));
      }
    } catch (error) {
      setResults(prev => ({ ...prev, [method]: { status: 'error', error: 'Connection failed' } }));
    } finally {
      setRunning(null);
    }
  };

  const getButtonContent = (method: string, label: string) => {
    if (running === method) {
      return (
        <span className="flex items-center justify-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Running...
        </span>
      );
    }
    return label;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Run Benchmark</h2>
        <p className="mt-1 text-sm text-gray-500">
          Execute performance tests for calculation methods
        </p>
      </div>
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* .NET Method */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-3">
              <div className="h-3 w-3 rounded-full bg-purple-600" />
              <h3 className="font-medium text-gray-900">.NET (DataTable)</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              C# implementation using DataTable.Compute
            </p>
            {results.dotnet?.status === 'success' && (
              <p className="text-sm text-green-600 mb-2">✓ Completed in {results.dotnet.time?.toFixed(2)}s</p>
            )}
            {results.dotnet?.status === 'error' && (
              <p className="text-sm text-red-600 mb-2">✗ {results.dotnet.error}</p>
            )}
            <button
              onClick={() => runBenchmark('dotnet')}
              disabled={running !== null}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {getButtonContent('dotnet', 'Run .NET')}
            </button>
          </div>
          
          {/* Python Method */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-3">
              <div className="h-3 w-3 rounded-full bg-blue-500" />
              <h3 className="font-medium text-gray-900">Python (eval)</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              Python implementation using safe eval() with ast
            </p>
            {results.python?.status === 'success' && (
              <p className="text-sm text-green-600 mb-2">✓ Completed in {results.python.time?.toFixed(2)}s</p>
            )}
            {results.python?.status === 'error' && (
              <p className="text-sm text-red-600 mb-2">✗ {results.python.error}</p>
            )}
            <button
              onClick={() => runBenchmark('python')}
              disabled={running !== null}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {getButtonContent('python', 'Run Python')}
            </button>
          </div>
          
          {/* SQL Method */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-3">
              <div className="h-3 w-3 rounded-full bg-orange-500" />
              <h3 className="font-medium text-gray-900">SQL (Dynamic)</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              PostgreSQL dynamic SQL stored procedures
            </p>
            {results.sql?.status === 'success' && (
              <p className="text-sm text-green-600 mb-2">✓ Completed in {results.sql.time?.toFixed(2)}s</p>
            )}
            {results.sql?.status === 'error' && (
              <p className="text-sm text-red-600 mb-2">✗ {results.sql.error}</p>
            )}
            <button
              onClick={() => runBenchmark('sql')}
              disabled={running !== null}
              className="w-full px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {getButtonContent('sql', 'Run SQL')}
            </button>
          </div>
        </div>
        
        <div className="flex justify-center pt-4">
          <button
            onClick={() => runBenchmark('all')}
            disabled={running !== null}
            className="px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {getButtonContent('all', 'Run All Methods')}
          </button>
        </div>
        
        <p className="text-center text-sm text-gray-500">
          Results will be saved to the database and displayed in the dashboard
        </p>
      </div>
    </div>
  );
}

/**
 * Main App component with layout structure
 */
function App() {
  const [activeSection, setActiveSection] = useState<NavigationSection>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNavigate = (section: string) => {
    setActiveSection(section as NavigationSection);
  };

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  /**
   * Render content based on active section
   */
  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <DashboardContent />;
      case 'formulas':
        return <FormulasContent />;
      case 'verification':
        return <VerificationContent />;
      case 'benchmark':
        return <BenchmarkContent />;
      default:
        return <DashboardContent />;
    }
  };

  /**
   * Get page title based on active section
   */
  const getPageTitle = () => {
    switch (activeSection) {
      case 'dashboard':
        return 'Dashboard Overview';
      case 'formulas':
        return 'Test Formulas';
      case 'verification':
        return 'Results Verification';
      case 'benchmark':
        return 'Run Benchmark';
      default:
        return 'Dashboard';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header
        activeSection={activeSection}
        onNavigate={handleNavigate}
        onMenuToggle={handleMenuToggle}
      />

      {/* Sidebar */}
      <Sidebar
        activeSection={activeSection}
        onNavigate={handleNavigate}
        isOpen={sidebarOpen}
        onClose={handleSidebarClose}
      />

      {/* Main content area */}
      <main className="lg:pl-64 pt-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Page header */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900">{getPageTitle()}</h2>
            <p className="mt-1 text-sm text-gray-500">
              {activeSection === 'dashboard' &&
                'Performance comparison between .NET, Python, and SQL calculation methods'}
              {activeSection === 'formulas' &&
                'Browse and manage test formulas for benchmarking'}
              {activeSection === 'verification' &&
                'Ensure all methods produce consistent results'}
              {activeSection === 'benchmark' &&
                'Execute and monitor performance tests'}
            </p>
          </div>

          {/* Content */}
          {renderContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
