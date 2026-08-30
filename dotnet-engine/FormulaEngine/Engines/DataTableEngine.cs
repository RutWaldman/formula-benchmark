using System.Data;
using System.Text.RegularExpressions;
using FormulaEngine.Models;

namespace FormulaEngine.Engines;

/// <summary>
/// Formula calculation engine using DataTable.Compute.
/// Transforms formula syntax to be compatible with DataTable expression syntax.
/// </summary>
public class DataTableEngine : IFormulaEngine
{
    /// <summary>
    /// Gets the name of this calculation engine.
    /// </summary>
    public string Name => "DotNet_DataTable";

    private readonly DataTable _dataTable;

    public DataTableEngine()
    {
        _dataTable = new DataTable();
        // Add columns for formula variables
        _dataTable.Columns.Add("a", typeof(double));
        _dataTable.Columns.Add("b", typeof(double));
        _dataTable.Columns.Add("c", typeof(double));
        _dataTable.Columns.Add("d", typeof(double));
    }

    /// <summary>
    /// Calculate a single formula for a specific data record.
    /// </summary>
    public double? CalculateFormula(Formula formula, DataRecord record)
    {
        try
        {
            // Clear any existing rows
            _dataTable.Rows.Clear();

            // Add the data record as a row
            var row = _dataTable.NewRow();
            row["a"] = record.A;
            row["b"] = record.B;
            row["c"] = record.C;
            row["d"] = record.D;
            _dataTable.Rows.Add(row);

            // Build the formula expression
            string expression = BuildExpression(formula, record);

            // For all formulas, we need to substitute variable values first
            // DataTable.Compute with column references doesn't work reliably
            // So we always use direct value substitution
            var mathResult = EvaluateWithMathFunctions(expression, record);
            return ValidateResult(mathResult);
        }
        catch (DivideByZeroException)
        {
            // Handle division by zero gracefully
            return null;
        }
        catch (OverflowException)
        {
            // Handle overflow for large numbers
            return null;
        }
        catch (Exception)
        {
            // Handle any other calculation errors gracefully
            return null;
        }
    }

    /// <summary>
    /// Validate a computed result to ensure it's a valid number.
    /// Returns null for NaN, Infinity, or null input values.
    /// </summary>
    private static double? ValidateResult(double? value)
    {
        if (!value.HasValue)
            return null;

        // Check for NaN and Infinity values
        if (double.IsNaN(value.Value) || double.IsInfinity(value.Value))
            return null;

        return value.Value;
    }

    /// <summary>
    /// Calculate a single formula for all data records.
    /// </summary>
    public CalculationResult[] CalculateFormula(Formula formula, IEnumerable<DataRecord> records)
    {
        var results = new List<CalculationResult>();

        foreach (var record in records)
        {
            var result = CalculateFormula(formula, record);
            results.Add(new CalculationResult
            {
                DataId = record.DataId,
                TargilId = formula.TargilId,
                Method = Name,
                Result = result
            });
        }

        return results.ToArray();
    }

    /// <summary>
    /// Calculate all formulas for all data records.
    /// </summary>
    public Dictionary<int, CalculationResult[]> CalculateAllFormulas(
        IEnumerable<Formula> formulas,
        IEnumerable<DataRecord> records)
    {
        var allResults = new Dictionary<int, CalculationResult[]>();
        var recordsList = records.ToList(); // Materialize once for multiple iterations

        foreach (var formula in formulas)
        {
            allResults[formula.TargilId] = CalculateFormula(formula, recordsList);
        }

        return allResults;
    }

    /// <summary>
    /// Build the complete expression, handling conditional formulas.
    /// </summary>
    private string BuildExpression(Formula formula, DataRecord record)
    {
        if (!string.IsNullOrEmpty(formula.Tnai))
        {
            // Conditional formula: use IIF function
            string condition = TransformFormula(formula.Tnai);
            string trueExpression = TransformFormula(formula.Targil);
            string falseExpression = !string.IsNullOrEmpty(formula.TargilFalse)
                ? TransformFormula(formula.TargilFalse)
                : "NULL";

            return $"IIF({condition}, {trueExpression}, {falseExpression})";
        }
        else
        {
            // Simple formula
            return TransformFormula(formula.Targil);
        }
    }

    /// <summary>
    /// Transform formula syntax to be compatible with DataTable.Compute.
    /// Converts mathematical functions to their DataTable equivalents.
    /// </summary>
    /// <param name="formula">The original formula string.</param>
    /// <returns>The transformed formula compatible with DataTable.Compute.</returns>
    public string TransformFormula(string formula)
    {
        if (string.IsNullOrEmpty(formula))
            return formula;

        string result = formula;

        // Convert if(condition, true_val, false_val) to IIF(condition, true_val, false_val)
        result = Regex.Replace(result, @"\bif\s*\(", "IIF(", RegexOptions.IgnoreCase);

        // Convert mathematical functions (case-insensitive)
        // sqrt -> Sqrt (DataTable.Compute doesn't support sqrt, need to use power)
        // Note: DataTable.Compute doesn't have Sqrt, so we need to handle it differently
        // We'll convert sqrt(x) to power calculation or use a workaround
        
        // First, handle sqrt by converting sqrt(expr) to a marker we'll process
        result = Regex.Replace(result, @"\bsqrt\s*\(([^)]+)\)", m =>
        {
            // DataTable doesn't support sqrt directly, but supports basic arithmetic
            // We can use: for sqrt(x), we compute it manually or use approximation
            // Actually, DataTable.Compute does NOT support Sqrt function
            // We need to evaluate sqrt separately
            // For now, we'll mark it for special handling
            return $"__SQRT__({m.Groups[1].Value})";
        }, RegexOptions.IgnoreCase);

        // Convert abs -> Abs (DataTable does NOT support Abs directly either)
        // We'll convert abs(x) to IIF(x < 0, -x, x)
        result = Regex.Replace(result, @"\babs\s*\(([^)]+)\)", m =>
        {
            string inner = m.Groups[1].Value;
            return $"IIF(({inner}) < 0, -({inner}), ({inner}))";
        }, RegexOptions.IgnoreCase);

        // Convert log -> we'll mark for special handling (DataTable doesn't support log)
        result = Regex.Replace(result, @"\blog\s*\(([^)]+)\)", m =>
        {
            return $"__LOG__({m.Groups[1].Value})";
        }, RegexOptions.IgnoreCase);

        // Convert power operator ^ to special marker
        // DataTable.Compute doesn't support ^ for power
        result = Regex.Replace(result, @"(\w+)\s*\^\s*(\d+)", m =>
        {
            string baseExpr = m.Groups[1].Value;
            string exponent = m.Groups[2].Value;
            return $"__POW__({baseExpr},{exponent})";
        });

        // Also handle expressions like (expr)^n
        result = Regex.Replace(result, @"\(([^)]+)\)\s*\^\s*(\d+)", m =>
        {
            string baseExpr = m.Groups[1].Value;
            string exponent = m.Groups[2].Value;
            return $"__POW__(({baseExpr}),{exponent})";
        });

        // Convert == to = for DataTable.Compute (uses = for equality)
        result = result.Replace("==", "=");

        // Convert != to <> for DataTable.Compute
        result = result.Replace("!=", "<>");

        return result;
    }

    /// <summary>
    /// Evaluate formula with mathematical functions using manual computation.
    /// Handles errors gracefully and returns null for invalid operations.
    /// </summary>
    private double? EvaluateWithMathFunctions(string formula, DataRecord record)
    {
        try
        {
            // Replace variable names with actual values
            string expr = formula;
            expr = Regex.Replace(expr, @"\ba\b", record.A.ToString(System.Globalization.CultureInfo.InvariantCulture));
            expr = Regex.Replace(expr, @"\bb\b", record.B.ToString(System.Globalization.CultureInfo.InvariantCulture));
            expr = Regex.Replace(expr, @"\bc\b", record.C.ToString(System.Globalization.CultureInfo.InvariantCulture));
            expr = Regex.Replace(expr, @"\bd\b", record.D.ToString(System.Globalization.CultureInfo.InvariantCulture));

            // Track if any math operation produced an invalid result
            bool hasInvalidResult = false;

            // Process __POW__(base,exp)
            expr = Regex.Replace(expr, @"__POW__\(([^,]+),(\d+)\)", m =>
            {
                try
                {
                    double baseVal = EvaluateSimpleExpression(m.Groups[1].Value);
                    if (double.IsNaN(baseVal) || double.IsInfinity(baseVal))
                    {
                        hasInvalidResult = true;
                        return "NaN";
                    }
                    int exp = int.Parse(m.Groups[2].Value);
                    double result = Math.Pow(baseVal, exp);
                    if (double.IsNaN(result) || double.IsInfinity(result))
                    {
                        hasInvalidResult = true;
                        return "NaN";
                    }
                    return result.ToString(System.Globalization.CultureInfo.InvariantCulture);
                }
                catch (OverflowException)
                {
                    hasInvalidResult = true;
                    return "NaN";
                }
            });

            // Process __SQRT__(expr)
            expr = Regex.Replace(expr, @"__SQRT__\(([^)]+)\)", m =>
            {
                double innerVal = EvaluateSimpleExpression(m.Groups[1].Value);
                if (double.IsNaN(innerVal) || double.IsInfinity(innerVal) || innerVal < 0)
                {
                    hasInvalidResult = true;
                    return "NaN";
                }
                double result = Math.Sqrt(innerVal);
                if (double.IsNaN(result) || double.IsInfinity(result))
                {
                    hasInvalidResult = true;
                    return "NaN";
                }
                return result.ToString(System.Globalization.CultureInfo.InvariantCulture);
            });

            // Process __LOG__(expr)
            expr = Regex.Replace(expr, @"__LOG__\(([^)]+)\)", m =>
            {
                double innerVal = EvaluateSimpleExpression(m.Groups[1].Value);
                if (double.IsNaN(innerVal) || double.IsInfinity(innerVal) || innerVal <= 0)
                {
                    hasInvalidResult = true;
                    return "NaN";
                }
                double result = Math.Log10(innerVal);
                if (double.IsNaN(result) || double.IsInfinity(result))
                {
                    hasInvalidResult = true;
                    return "NaN";
                }
                return result.ToString(System.Globalization.CultureInfo.InvariantCulture);
            });

            // If any math operation produced an invalid result, return null early
            if (hasInvalidResult || expr.Contains("NaN"))
                return null;

            // Now evaluate the remaining expression using DataTable
            var dt = new DataTable();
            var result = dt.Compute(expr, null);
            if (result == null || result == DBNull.Value)
                return null;
                
            double computedValue = Convert.ToDouble(result);
            
            // Validate the final result
            if (double.IsNaN(computedValue) || double.IsInfinity(computedValue))
                return null;
                
            return computedValue;
        }
        catch (DivideByZeroException)
        {
            return null;
        }
        catch (OverflowException)
        {
            return null;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Evaluate a simple numeric expression.
    /// Returns NaN for any errors or invalid operations.
    /// </summary>
    private double EvaluateSimpleExpression(string expr)
    {
        try
        {
            var dt = new DataTable();
            var result = dt.Compute(expr, null);
            
            if (result == null || result == DBNull.Value)
                return double.NaN;
                
            double value = Convert.ToDouble(result);
            
            // Check for NaN and Infinity
            if (double.IsNaN(value) || double.IsInfinity(value))
                return double.NaN;
                
            return value;
        }
        catch (DivideByZeroException)
        {
            return double.NaN;
        }
        catch (OverflowException)
        {
            return double.NaN;
        }
        catch
        {
            return double.NaN;
        }
    }
}
