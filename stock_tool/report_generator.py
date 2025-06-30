import pandas as pd
from tabulate import tabulate

class ReportGenerator:
    def display_console(self, results, preferences):
        """Display analysis results in a formatted console table."""
        columns = preferences.get('console_columns', ['ticker', 'score', 'intrinsic_value', 'price'])
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        table_data = [{col: stock.get(col, 'N/A') for col in columns} for stock in sorted_results]
        print(tabulate(table_data, headers='keys', tablefmt='psql'))

    def generate_csv(self, results, preferences, output_dir):
        """Generate CSV files from analysis results, with optional sector grouping."""
        df = pd.DataFrame(results)
        columns = preferences.get('csv_columns', ['ticker', 'sector', 'score', 'intrinsic_value', 'price'])
        if preferences.get('group_by_sector', False):
            for sector, group in df.groupby('sector'):
                group[columns].to_csv(f"{output_dir}/{sector}.csv", index=False)
        else:
            df[columns].to_csv(f"{output_dir}/all_stocks.csv", index=False)

    def summarize_metrics(self, results, preferences):
        """Summarize key metrics by sector and print the results."""
        df = pd.DataFrame(results)
        agg_funcs = {
            'count': ('ticker', 'count'),
            'average_score': ('score', 'mean'),
            'average_price': ('price', 'mean'),
            'min_score': ('score', 'min'),
            'max_score': ('score', 'max'),
        }
        selected_metrics = preferences.get('summary_metrics', ['count', 'average_score'])
        agg_dict = {metric: agg_funcs[metric] for metric in selected_metrics if metric in agg_funcs}
        summary = df.groupby('sector').agg(**{name: (col, func) for name, (col, func) in agg_dict.items()})
        print(summary)