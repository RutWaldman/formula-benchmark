namespace FormulaEngine.Models;

/// <summary>
/// Represents a formula definition from the t_targil table.
/// Contains the formula expression and optional conditional logic.
/// </summary>
public class Formula
{
    /// <summary>
    /// Unique identifier for the formula (Primary Key).
    /// </summary>
    public int TargilId { get; set; }

    /// <summary>
    /// The main formula expression string (e.g., "a + b", "sqrt(c^2 + d^2)").
    /// </summary>
    public string Targil { get; set; } = string.Empty;

    /// <summary>
    /// Optional condition expression for conditional formulas (e.g., "a > 5").
    /// When present, determines whether to use Targil or TargilFalse.
    /// </summary>
    public string? Tnai { get; set; }

    /// <summary>
    /// Optional formula to use when the condition (Tnai) evaluates to false.
    /// Only used when Tnai is specified.
    /// </summary>
    public string? TargilFalse { get; set; }
}
