# Screenshots Directory

This directory contains screenshots documenting the database structure and dashboard for the Dynamic Formula Benchmark System.

## Required Screenshots

The following screenshots should be captured and added to this directory:

### Database Screenshots

| Filename | Description | How to Capture |
|----------|-------------|----------------|
| `database_t_data.png` | Sample of t_data table (first 50-100 records) | pgAdmin: Query `SELECT * FROM t_data LIMIT 100` |
| `database_t_targil.png` | All formulas in t_targil table | pgAdmin: Query `SELECT * FROM t_targil` |
| `database_t_results.png` | Sample of t_results table with results from all methods | pgAdmin: Query `SELECT * FROM t_results LIMIT 100` |

### Dashboard Screenshots

| Filename | Description | How to Capture |
|----------|-------------|----------------|
| `dashboard_overview.png` | Main dashboard view showing all components | Browser screenshot of deployed dashboard |
| `dashboard_chart.png` | Performance comparison chart (bar/line chart) | Browser screenshot of chart section |

## Capture Instructions

### Using pgAdmin (Database Screenshots)

1. Open pgAdmin and connect to the PostgreSQL database
2. Open Query Tool (Tools → Query Tool)
3. Run the appropriate query from the table above
4. Right-click on the result grid → Screenshot or use system screenshot tool
5. Save the screenshot with the correct filename in this directory

**Recommended Queries:**

```sql
-- For t_data screenshot
SELECT data_id, a, b, c, d FROM t_data ORDER BY data_id LIMIT 100;

-- For t_targil screenshot (shows all formulas)
SELECT targil_id, targil, tnai, targil_false, description, complexity_level FROM t_targil ORDER BY targil_id;

-- For t_results screenshot
SELECT 
    r.results_id, 
    r.data_id, 
    r.targil_id, 
    r.method, 
    ROUND(r.result::numeric, 4) as result
FROM t_results r 
ORDER BY r.data_id, r.targil_id, r.method 
LIMIT 100;

-- For t_log screenshot (performance data)
SELECT 
    log_id, 
    targil_id, 
    method, 
    ROUND(run_time::numeric, 4) as run_time_seconds,
    created_at
FROM t_log 
ORDER BY targil_id, method;
```

### Using Browser (Dashboard Screenshots)

1. Navigate to the deployed dashboard URL (Vercel deployment)
2. Ensure all data is loaded and charts are rendered
3. Use browser screenshot tool or system screenshot (Windows: Win+Shift+S, Mac: Cmd+Shift+4)
4. For full page: Use browser extension like "Full Page Screen Capture" or browser DevTools
5. Save screenshots with the correct filenames

### Alternative: Using DBeaver

If using DBeaver instead of pgAdmin:
1. Connect to the PostgreSQL database
2. Run the query in SQL Editor
3. Right-click on results → Export → Image
4. Save with the appropriate filename

### Alternative: Using Command Line

```bash
# Export query results to CSV for reference
psql -h localhost -U postgres -d formula_benchmark -c "\COPY (SELECT * FROM t_data LIMIT 100) TO 'docs/screenshots/t_data_sample.csv' CSV HEADER"
```

## Placeholder Files

The following placeholder files indicate which screenshots are needed:

- [ ] `database_t_data.png` - Awaiting capture
- [ ] `database_t_targil.png` - Awaiting capture  
- [ ] `database_t_results.png` - Awaiting capture
- [ ] `dashboard_overview.png` - Awaiting capture
- [ ] `dashboard_chart.png` - Awaiting capture

## Notes

- Screenshots should be clear and readable
- Use a reasonable resolution (at least 1280x720)
- Ensure no sensitive data (passwords, connection strings) is visible
- Crop screenshots to show relevant content only
- Use PNG format for best quality

## Requirements Reference

This task fulfills **Requirement 7.6**: THE System SHALL include database screenshots showing sample data.
