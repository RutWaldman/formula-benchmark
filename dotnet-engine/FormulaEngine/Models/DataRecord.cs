namespace FormulaEngine.Models;

/// <summary>
/// Represents a single data record from the t_data table.
/// Contains numeric values for formula calculations.
/// </summary>
public class DataRecord
{
    /// <summary>
    /// Unique identifier for the data record (Primary Key).
    /// </summary>
    public int DataId { get; set; }

    /// <summary>
    /// Numeric value A for formula calculations.
    /// </summary>
    public double A { get; set; }

    /// <summary>
    /// Numeric value B for formula calculations.
    /// </summary>
    public double B { get; set; }

    /// <summary>
    /// Numeric value C for formula calculations.
    /// </summary>
    public double C { get; set; }

    /// <summary>
    /// Numeric value D for formula calculations.
    /// </summary>
    public double D { get; set; }
}
