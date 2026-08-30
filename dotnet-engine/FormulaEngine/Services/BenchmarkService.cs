using System.Diagnostics;
using FormulaEngine.Engines;
using FormulaEngine.Models;
using FormulaEngine.Repositories;

namespace FormulaEngine.Services;

/// <summary>
/// Service that orchestrates the formula benchmark execution.
/// Coordinates data loading, formula calculation, and result persistence.
/// </summary>
public class BenchmarkService
{
    private readonly IDataRepository _repository;
    private readonly IFormulaEngine _engine;

    public BenchmarkService(IDataRepository repository, IFormulaEngine engine)
    {
        _repository = repository;
        _engine = engine;
    }

    /// <summary>
    /// Run the complete benchmark for all formulas.
    /// Measures execution time per formula and saves results to the database.
    /// </summary>
    public async Task<BenchmarkSummary> RunBenchmarkAsync()
    {
        var summary = new BenchmarkSummary
        {
            Method = _engine.Name,
            StartTime = DateTime.Now
        };

        var totalStopwatch = Stopwatch.StartNew();

        try
        {
            Console.WriteLine($"\n{'=',-60}");
            Console.WriteLine($"Starting benchmark for method: {_engine.Name}");
            Console.WriteLine($"{'=',-60}\n");

            // Clear previous results for this method
            Console.WriteLine("Clearing previous results...");
            await _repository.ClearMethodResultsAsync(_engine.Name);
            await _repository.ClearMethodLogsAsync(_engine.Name);

            // Load data records
            Console.WriteLine("Loading data records from database...");
            var dataLoadStopwatch = Stopwatch.StartNew();
            var dataRecords = (await _repository.GetAllDataRecordsAsync()).ToList();
            dataLoadStopwatch.Stop();
            Console.WriteLine($"Loaded {dataRecords.Count:N0} data records in {dataLoadStopwatch.Elapsed.TotalSeconds:F2}s\n");

            summary.TotalRecords = dataRecords.Count;

            // Load formulas
            Console.WriteLine("Loading formulas from database...");
            var formulas = (await _repository.GetAllFormulasAsync()).ToList();
            Console.WriteLine($"Found {formulas.Count} formulas to process\n");

            summary.TotalFormulas = formulas.Count;

            // Process each formula
            foreach (var formula in formulas)
            {
                var formulaResult = await ProcessFormulaAsync(formula, dataRecords);
                summary.FormulaResults.Add(formulaResult);
            }

            totalStopwatch.Stop();
            summary.TotalTime = totalStopwatch.Elapsed.TotalSeconds;
            summary.EndTime = DateTime.Now;

            // Print summary
            PrintSummary(summary);

            return summary;
        }
        catch (Exception ex)
        {
            totalStopwatch.Stop();
            Console.WriteLine($"\nBenchmark failed with error: {ex.Message}");
            throw;
        }
    }

    /// <summary>
    /// Process a single formula: calculate results for all data records,
    /// measure execution time, and save to database.
    /// </summary>
    private async Task<FormulaResult> ProcessFormulaAsync(Formula formula, List<DataRecord> dataRecords)
    {
        var formulaDisplay = GetFormulaDisplay(formula);
        Console.WriteLine($"Processing formula {formula.TargilId}: {formulaDisplay}");

        var stopwatch = Stopwatch.StartNew();

        // Calculate results for all data records
        var results = _engine.CalculateFormula(formula, dataRecords);

        stopwatch.Stop();
        var executionTime = stopwatch.Elapsed.TotalSeconds;

        // Save results to database
        Console.Write($"  Calculated {results.Length:N0} results in {executionTime:F3}s - Saving...");
        await _repository.SaveResultsBatchAsync(results);
        Console.WriteLine(" Done");

        // Save timing log
        await _repository.SaveLogEntryAsync(formula.TargilId, _engine.Name, executionTime);

        // Count valid/null results
        var validResults = results.Count(r => r.Result.HasValue);
        var nullResults = results.Length - validResults;

        Console.WriteLine($"  Valid results: {validResults:N0}, Null results: {nullResults:N0}\n");

        return new FormulaResult
        {
            TargilId = formula.TargilId,
            Formula = formulaDisplay,
            ExecutionTime = executionTime,
            RecordsProcessed = results.Length,
            ValidResults = validResults,
            NullResults = nullResults
        };
    }

    /// <summary>
    /// Get a display string for the formula, including condition if present.
    /// </summary>
    private static string GetFormulaDisplay(Formula formula)
    {
        if (!string.IsNullOrEmpty(formula.Tnai))
        {
            var falseFormula = formula.TargilFalse ?? "null";
            return $"if({formula.Tnai}, {formula.Targil}, {falseFormula})";
        }
        return formula.Targil;
    }

    /// <summary>
    /// Print the benchmark summary to the console.
    /// </summary>
    private static void PrintSummary(BenchmarkSummary summary)
    {
        Console.WriteLine($"\n{'=',-60}");
        Console.WriteLine("BENCHMARK SUMMARY");
        Console.WriteLine($"{'=',-60}");
        Console.WriteLine($"Method:           {summary.Method}");
        Console.WriteLine($"Total Records:    {summary.TotalRecords:N0}");
        Console.WriteLine($"Total Formulas:   {summary.TotalFormulas}");
        Console.WriteLine($"Total Time:       {summary.TotalTime:F2} seconds");
        Console.WriteLine($"Start Time:       {summary.StartTime:yyyy-MM-dd HH:mm:ss}");
        Console.WriteLine($"End Time:         {summary.EndTime:yyyy-MM-dd HH:mm:ss}");
        Console.WriteLine($"\nPer-Formula Results:");
        Console.WriteLine($"{"-",-60}");
        Console.WriteLine($"{"ID",-4} {"Formula",-35} {"Time (s)",-10} {"Valid",-12}");
        Console.WriteLine($"{"-",-60}");

        foreach (var result in summary.FormulaResults)
        {
            var formulaShort = result.Formula.Length > 32 
                ? result.Formula.Substring(0, 29) + "..." 
                : result.Formula;
            Console.WriteLine($"{result.TargilId,-4} {formulaShort,-35} {result.ExecutionTime,-10:F3} {result.ValidResults:N0}");
        }

        Console.WriteLine($"{'=',-60}\n");
    }
}

/// <summary>
/// Summary of a complete benchmark run.
/// </summary>
public class BenchmarkSummary
{
    public string Method { get; set; } = string.Empty;
    public int TotalRecords { get; set; }
    public int TotalFormulas { get; set; }
    public double TotalTime { get; set; }
    public DateTime StartTime { get; set; }
    public DateTime EndTime { get; set; }
    public List<FormulaResult> FormulaResults { get; } = new();
}

/// <summary>
/// Result of processing a single formula.
/// </summary>
public class FormulaResult
{
    public int TargilId { get; set; }
    public string Formula { get; set; } = string.Empty;
    public double ExecutionTime { get; set; }
    public int RecordsProcessed { get; set; }
    public int ValidResults { get; set; }
    public int NullResults { get; set; }
}
