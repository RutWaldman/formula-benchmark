/**
 * Static benchmark data for deployment without backend
 * Contains actual benchmark results from the system
 */

import type {
  BenchmarkResult,
  MethodComparison,
  VerificationResult,
  Formula,
} from '../types';

export const STATIC_BENCHMARK_RESULTS: BenchmarkResult[] = [
  { targilId: 1, formula: "a + b", description: "Simple addition of a and b", complexityLevel: "simple", dotnetTime: 5.1289279, pythonTime: 46.0239721997641, sqlTime: 21.965377 },
  { targilId: 2, formula: "c * 2", description: "Simple multiplication of c by 2", complexityLevel: "simple", dotnetTime: 4.9928296, pythonTime: 45.082318999804556, sqlTime: 25.633723 },
  { targilId: 3, formula: "b - a", description: "Simple subtraction: b minus a", complexityLevel: "simple", dotnetTime: 10.7751512, pythonTime: 45.373571699950844, sqlTime: 25.292471 },
  { targilId: 4, formula: "d / 4", description: "Simple division of d by 4", complexityLevel: "simple", dotnetTime: 5.0002932, pythonTime: 49.19037530012429, sqlTime: 24.491274 },
  { targilId: 5, formula: "(a + b) * 8", description: "Complex expression with parentheses", complexityLevel: "complex", dotnetTime: 5.1538976, pythonTime: 52.222764699719846, sqlTime: 23.16024 },
  { targilId: 6, formula: "sqrt(c * c + d * d)", description: "Pythagorean theorem - distance calculation", complexityLevel: "complex", dotnetTime: 11.835762, pythonTime: 60.65119320014492, sqlTime: 42.009672 },
  { targilId: 7, formula: "log(b) + c", description: "Logarithmic calculation plus c", complexityLevel: "complex", dotnetTime: 19.1171721, pythonTime: 52.30407200008631, sqlTime: 38.803976 },
  { targilId: 8, formula: "abs(d - b)", description: "Absolute value of difference", complexityLevel: "complex", dotnetTime: 20.1124199, pythonTime: 53.0121944998391, sqlTime: 42.427881 },
  { targilId: 9, formula: "if(a > 5, b * 2, b / 2)", description: "If a > 5 then b*2 else b/2", complexityLevel: "conditional", dotnetTime: 18.9115603, pythonTime: 61.960714700166136, sqlTime: 42.524641 },
  { targilId: 10, formula: "if(b < 10, a + 1, d - 1)", description: "If b < 10 then a+1 else d-1", complexityLevel: "conditional", dotnetTime: 17.6228463, pythonTime: 60.4333843998611, sqlTime: 41.264825 },
  { targilId: 11, formula: "if(a == c, 1, 0)", description: "Equality check: if a equals c return 1 else 0", complexityLevel: "conditional", dotnetTime: 15.0945672, pythonTime: 184.6613265001215, sqlTime: 44.476695 },
];

export const STATIC_FORMULAS: Formula[] = [
  { targilId: 1, targil: "a + b", tnai: null, targilFalse: null, description: "Simple addition", complexityLevel: "simple" },
  { targilId: 2, targil: "c * 2", tnai: null, targilFalse: null, description: "Simple multiplication", complexityLevel: "simple" },
  { targilId: 3, targil: "b - a", tnai: null, targilFalse: null, description: "Simple subtraction", complexityLevel: "simple" },
  { targilId: 4, targil: "d / 4", tnai: null, targilFalse: null, description: "Simple division", complexityLevel: "simple" },
  { targilId: 5, targil: "(a + b) * 8", tnai: null, targilFalse: null, description: "Complex with parentheses", complexityLevel: "complex" },
  { targilId: 6, targil: "sqrt(c * c + d * d)", tnai: null, targilFalse: null, description: "Pythagorean theorem", complexityLevel: "complex" },
  { targilId: 7, targil: "log(b) + c", tnai: null, targilFalse: null, description: "Logarithmic calculation", complexityLevel: "complex" },
  { targilId: 8, targil: "abs(d - b)", tnai: null, targilFalse: null, description: "Absolute value", complexityLevel: "complex" },
  { targilId: 9, targil: "b * 2", tnai: "a > 5", targilFalse: "b / 2", description: "Conditional multiplication/division", complexityLevel: "conditional" },
  { targilId: 10, targil: "a + 1", tnai: "b < 10", targilFalse: "d - 1", description: "Conditional addition/subtraction", complexityLevel: "conditional" },
  { targilId: 11, targil: "1", tnai: "a == c", targilFalse: "0", description: "Equality check", complexityLevel: "conditional" },
];

export const STATIC_COMPARISON: MethodComparison[] = [
  {
    method: "DotNet_DataTable",
    displayName: ".NET (DataTable)",
    totalTime: 133.7454273,
    averageTime: 12.158675209090909,
    formulasProcessed: 11,
    color: "#512BD4",
  },
  {
    method: "Python_Eval",
    displayName: "Python (eval)",
    totalTime: 710.9164930999577,
    averageTime: 64.62877209999616,
    formulasProcessed: 11,
    color: "#3776AB",
  },
  {
    method: "SQL_Dynamic",
    displayName: "SQL (Dynamic)",
    totalTime: 372.050775,
    averageTime: 33.82279772727273,
    formulasProcessed: 11,
    color: "#F29111",
  },
];

export const STATIC_VERIFICATION: VerificationResult = {
  isValid: true,
  totalRecordsChecked: 11000000,
  discrepancies: [],
  methodsCompared: ["DotNet_DataTable", "Python_Eval", "SQL_Dynamic"],
  timestamp: "2026-08-30T06:31:40.681404",
};

// Flag to determine if we should use static data
export const USE_STATIC_DATA = import.meta.env.VITE_USE_STATIC_DATA === 'true' || 
  !import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_BASE_URL === '';
