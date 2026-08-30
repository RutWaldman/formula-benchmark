using System.Text;
using FormulaEngine.Models;
using Npgsql;

namespace FormulaEngine.Repositories;

/// <summary>
/// PostgreSQL implementation of the data repository.
/// Uses Npgsql for database access with optimized batch operations.
/// </summary>
public class PostgresRepository : IDataRepository
{
    private readonly string _connectionString;
    private NpgsqlConnection? _connection;
    private const int BatchSize = 10000;

    public PostgresRepository(string connectionString)
    {
        _connectionString = connectionString;
    }

    /// <summary>
    /// Initialize the repository and establish database connection.
    /// </summary>
    public async Task InitializeAsync()
    {
        _connection = new NpgsqlConnection(_connectionString);
        await _connection.OpenAsync();
        Console.WriteLine("Database connection established.");
    }

    /// <summary>
    /// Get all data records from the t_data table.
    /// Uses streaming for memory efficiency with large datasets.
    /// </summary>
    public async Task<IEnumerable<DataRecord>> GetAllDataRecordsAsync()
    {
        EnsureConnectionOpen();

        var records = new List<DataRecord>();
        const string query = "SELECT data_id, a, b, c, d FROM t_data ORDER BY data_id";

        await using var cmd = new NpgsqlCommand(query, _connection);
        await using var reader = await cmd.ExecuteReaderAsync();

        while (await reader.ReadAsync())
        {
            records.Add(new DataRecord
            {
                DataId = reader.GetInt32(0),
                A = reader.GetDouble(1),
                B = reader.GetDouble(2),
                C = reader.GetDouble(3),
                D = reader.GetDouble(4)
            });
        }

        return records;
    }

    /// <summary>
    /// Get all formulas from the t_targil table.
    /// </summary>
    public async Task<IEnumerable<Formula>> GetAllFormulasAsync()
    {
        EnsureConnectionOpen();

        var formulas = new List<Formula>();
        const string query = "SELECT targil_id, targil, tnai, targil_false FROM t_targil ORDER BY targil_id";

        await using var cmd = new NpgsqlCommand(query, _connection);
        await using var reader = await cmd.ExecuteReaderAsync();

        while (await reader.ReadAsync())
        {
            formulas.Add(new Formula
            {
                TargilId = reader.GetInt32(0),
                Targil = reader.GetString(1),
                Tnai = reader.IsDBNull(2) ? null : reader.GetString(2),
                TargilFalse = reader.IsDBNull(3) ? null : reader.GetString(3)
            });
        }

        return formulas;
    }

    /// <summary>
    /// Save calculation results to the t_results table using bulk insert.
    /// Uses COPY command for optimal performance with large datasets.
    /// </summary>
    public async Task SaveResultsBatchAsync(IEnumerable<CalculationResult> results)
    {
        EnsureConnectionOpen();

        var resultsList = results.ToList();
        if (resultsList.Count == 0) return;

        // Use COPY command for bulk insert (most efficient for PostgreSQL)
        await using var writer = await _connection!.BeginBinaryImportAsync(
            "COPY t_results (data_id, targil_id, method, result) FROM STDIN (FORMAT BINARY)");

        foreach (var result in resultsList)
        {
            await writer.StartRowAsync();
            await writer.WriteAsync(result.DataId, NpgsqlTypes.NpgsqlDbType.Integer);
            await writer.WriteAsync(result.TargilId, NpgsqlTypes.NpgsqlDbType.Integer);
            await writer.WriteAsync(result.Method, NpgsqlTypes.NpgsqlDbType.Varchar);
            
            if (result.Result.HasValue)
            {
                await writer.WriteAsync(result.Result.Value, NpgsqlTypes.NpgsqlDbType.Double);
            }
            else
            {
                await writer.WriteNullAsync();
            }
        }

        await writer.CompleteAsync();
    }

    /// <summary>
    /// Save a log entry with execution timing to the t_log table.
    /// </summary>
    public async Task SaveLogEntryAsync(int targilId, string method, double runTime)
    {
        EnsureConnectionOpen();

        const string query = @"
            INSERT INTO t_log (targil_id, method, run_time)
            VALUES (@targilId, @method, @runTime)";

        await using var cmd = new NpgsqlCommand(query, _connection);
        cmd.Parameters.AddWithValue("targilId", targilId);
        cmd.Parameters.AddWithValue("method", method);
        cmd.Parameters.AddWithValue("runTime", runTime);

        await cmd.ExecuteNonQueryAsync();
    }

    /// <summary>
    /// Clear previous results for a specific calculation method.
    /// </summary>
    public async Task ClearMethodResultsAsync(string method)
    {
        EnsureConnectionOpen();

        const string query = "DELETE FROM t_results WHERE method = @method";

        await using var cmd = new NpgsqlCommand(query, _connection);
        cmd.Parameters.AddWithValue("method", method);

        var deleted = await cmd.ExecuteNonQueryAsync();
        Console.WriteLine($"Cleared {deleted:N0} previous results for method '{method}'.");
    }

    /// <summary>
    /// Clear previous log entries for a specific calculation method.
    /// </summary>
    public async Task ClearMethodLogsAsync(string method)
    {
        EnsureConnectionOpen();

        const string query = "DELETE FROM t_log WHERE method = @method";

        await using var cmd = new NpgsqlCommand(query, _connection);
        cmd.Parameters.AddWithValue("method", method);

        var deleted = await cmd.ExecuteNonQueryAsync();
        Console.WriteLine($"Cleared {deleted:N0} previous log entries for method '{method}'.");
    }

    /// <summary>
    /// Ensure the database connection is open.
    /// </summary>
    private void EnsureConnectionOpen()
    {
        if (_connection == null || _connection.State != System.Data.ConnectionState.Open)
        {
            throw new InvalidOperationException("Database connection is not open. Call InitializeAsync() first.");
        }
    }

    /// <summary>
    /// Dispose of the database connection.
    /// </summary>
    public async ValueTask DisposeAsync()
    {
        if (_connection != null)
        {
            await _connection.CloseAsync();
            await _connection.DisposeAsync();
            _connection = null;
            Console.WriteLine("Database connection closed.");
        }
    }
}
