using FormulaEngine.Models;

namespace FormulaEngine.Engines;

/// <summary>
/// Interface for formula calculation engines.
/// Defines the contract for all calculation methods to implement.
/// </summary>
public interface IFormulaEngine
{
    /// <summary>
    /// Gets the name of the calculation engine (e.g., "DotNet_DataTable").
    /// </summary>
    string Name { get; }

    /// <summary>
    /// Calculate a single formula for a specific data record.
    /// </summary>
    /// <param name="formula">The formula definition to calculate.</param>
    /// <param name="record">The data record containing variable values (a, b, c, d).</param>
    /// <returns>The calculation result, or null if calculation failed.</returns>
    double? CalculateFormula(Formula formula, DataRecord record);

    /// <summary>
    /// Calculate a single formula for all data records.
    /// </summary>
    /// <param name="formula">The formula definition to calculate.</param>
    /// <param name="records">Collection of data records to process.</param>
    /// <returns>Array of calculation results for each data record.</returns>
    CalculationResult[] CalculateFormula(Formula formula, IEnumerable<DataRecord> records);

    /// <summary>
    /// Calculate all formulas for all data records.
    /// </summary>
    /// <param name="formulas">Collection of formulas to calculate.</param>
    /// <param name="records">Collection of data records to process.</param>
    /// <returns>Dictionary mapping formula ID to array of calculation results.</returns>
    Dictionary<int, CalculationResult[]> CalculateAllFormulas(
        IEnumerable<Formula> formulas, 
        IEnumerable<DataRecord> records);
}
