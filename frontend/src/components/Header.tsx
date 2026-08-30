/**
 * Header component for the Dynamic Formula Benchmark Dashboard
 * Displays the application title and navigation elements
 * 
 * Validates: Requirements 6.2
 */

interface HeaderProps {
  /** Currently active navigation section */
  activeSection: string;
  /** Callback when navigation item is clicked */
  onNavigate: (section: string) => void;
  /** Callback to toggle mobile sidebar */
  onMenuToggle: () => void;
}

/**
 * Navigation items for the header
 */
const navItems = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'formulas', label: 'Formulas' },
  { id: 'verification', label: 'Verification' },
  { id: 'benchmark', label: 'Run Benchmark' },
];

/**
 * Header component with responsive navigation
 */
export function Header({ activeSection, onNavigate, onMenuToggle }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Mobile menu button */}
        <button
          type="button"
          className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
          onClick={onMenuToggle}
          aria-label="Toggle navigation menu"
        >
          <svg
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>

        {/* Logo and title */}
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg
                className="h-5 w-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
          </div>
          <div className="hidden sm:block">
            <h1 className="text-xl font-bold text-gray-900">
              Dynamic Formula Benchmark
            </h1>
            <p className="text-xs text-gray-500">
              .NET vs Python vs SQL Performance Comparison
            </p>
          </div>
          {/* Mobile title - shorter */}
          <div className="sm:hidden">
            <h1 className="text-lg font-bold text-gray-900">Formula Benchmark</h1>
          </div>
        </div>

        {/* Desktop navigation */}
        <nav className="hidden lg:flex items-center space-x-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeSection === item.id
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Status indicator */}
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <span>Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
