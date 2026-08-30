using FormulaEngine.Models;

namespace FormulaEngine.Repositories;

/// <summary>
/// Interface for data repository operations.
/// Abstracts database access for formulas, data records, and results.
/// </summary>
public interface IDataRepository : IAsyncDisposable
{
    /// <summary>
    /// Initialize the repository and establish database connection.
    /// </summary>
    Task InitializeAsync();

    /// <summary>
    /// Get all data records from the t_data table.
    /// </summary>
    /// <returns>Enumerable of all data records.</returns>
    Task<IEnumerable<DataRecord>> GetAllDataRecordsAsync();

    /// <summary>
    /// Get all formulas from the t_targil table.
    /// </summary>
    /// <returns>Enumerable of all formula definitions.</returns>
    Task<IEnumerable<Formula>> GetAllFormulasAsync();

    /// <summary>
    /// Save calculation results to the t_results table in batches.
    /// </summary>
    /// <param name="results">Collection of calculation results to save.</param>
    Task SaveResultsBatchAsync(IEnumerable<CalculationResult> results);

    /// <summary>
    /// Save a log entry with execution timing to the t_log table.
    /// </summary>
    /// <param name="targilId">The formula ID.</param>
    /// <param name="method">The calculation method name.</param>
    /// <param name="runTime">Execution time in seconds.</param>
    Task SaveLogEntryAsync(int targilId, string method, double runTime);

    /// <summary>
    /// Clear previous results for a specific calculation method.
    /// </summary>
    /// <param name="method">The calculation method name to clear results for.</param>
    Task ClearMethodResultsAsync(string method);

    /// <summary>
    /// Clear previous log entries for a specific calculation method.
    /// </summary>
    /// <param name="method">The calculation method name to clear logs for.</param>
    Task ClearMethodLogsAsync(string method);
}
