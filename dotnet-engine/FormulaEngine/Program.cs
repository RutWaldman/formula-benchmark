using Microsoft.Extensions.Configuration;
using FormulaEngine.Engines;
using FormulaEngine.Repositories;
using FormulaEngine.Services;

namespace FormulaEngine;

/// <summary>
/// Main entry point for the Formula Engine benchmark application.
/// Loads configuration, initializes services, and runs the benchmark.
/// </summary>
class Program
{
    static async Task<int> Main(string[] args)
    {
        Console.WriteLine("Formula Engine - Dynamic Formula Benchmark");
        Console.WriteLine("==========================================");
        Console.WriteLine($".NET {Environment.Version}");
        Console.WriteLine($"Started at: {DateTime.Now:yyyy-MM-dd HH:mm:ss}\n");

        try
        {
            // Load configuration
            var configuration = new ConfigurationBuilder()
                .SetBasePath(Directory.GetCurrentDirectory())
                .AddJsonFile("appsettings.json", optional: false, reloadOnChange: false)
                .Build();

            var connectionString = configuration.GetConnectionString("PostgreSQL");
            if (string.IsNullOrEmpty(connectionString))
            {
                Console.WriteLine("Error: PostgreSQL connection string not found in appsettings.json");
                return 1;
            }

            Console.WriteLine("Configuration loaded successfully.");

            // Initialize repository
            await using var repository = new PostgresRepository(connectionString);
            await repository.InitializeAsync();

            // Initialize calculation engine
            var engine = new DataTableEngine();
            Console.WriteLine($"Using calculation engine: {engine.Name}");

            // Create and run benchmark service
            var benchmarkService = new BenchmarkService(repository, engine);
            var summary = await benchmarkService.RunBenchmarkAsync();

            // Final status
            Console.WriteLine("Benchmark completed successfully!");
            Console.WriteLine($"Total execution time: {summary.TotalTime:F2} seconds");
            Console.WriteLine($"Results saved to t_results table");
            Console.WriteLine($"Timing logs saved to t_log table");

            return 0;
        }
        catch (FileNotFoundException ex)
        {
            Console.WriteLine($"Configuration error: {ex.Message}");
            Console.WriteLine("Make sure appsettings.json exists in the working directory.");
            return 1;
        }
        catch (Npgsql.NpgsqlException ex)
        {
            Console.WriteLine($"Database error: {ex.Message}");
            Console.WriteLine("Check your database connection string and ensure PostgreSQL is running.");
            return 1;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Unexpected error: {ex.Message}");
            Console.WriteLine($"Stack trace: {ex.StackTrace}");
            return 1;
        }
    }
}
