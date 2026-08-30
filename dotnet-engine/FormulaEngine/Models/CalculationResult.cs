namespace FormulaEngine.Models;

/// <summary>
/// Represents a calculation result to be stored in the t_results table.
/// Links a data record with a formula and the computed result.
/// </summary>
public class CalculationResult
{
    /// <summary>
    /// Reference to the data record used in the calculation.
    /// </summary>
    public int DataId { get; set; }

    /// <summary>
    /// Reference to the formula used for the calculation.
    /// </summary>
    public int TargilId { get; set; }

    /// <summary>
    /// Name of the calculation method used (e.g., "DotNet_DataTable").
    /// </summary>
    public string Method { get; set; } = string.Empty;

    /// <summary>
    /// The calculated result value. 
    /// May be null if the calculation resulted in an error (e.g., division by zero).
    /// </summary>
    public double? Result { get; set; }
}
