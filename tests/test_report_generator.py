import pytest
import pandas as pd
from stock_tool.report_generator import ReportGenerator
from pathlib import Path

@pytest.fixture
def analysis_results():
    """Provide sample analysis results for testing."""
    return [
        {'ticker': 'AAPL', 'score': 1.5, 'intrinsic_value': 160.0, 'price': 150.0, 'sector': 'Technology'},
        {'ticker': 'MSFT', 'score': 1.2, 'intrinsic_value': 220.0, 'price': 200.0, 'sector': 'Technology'},
        {'ticker': 'JNJ', 'score': 1.1, 'intrinsic_value': 170.0, 'price': 160.0, 'sector': 'Healthcare'}
    ]

@pytest.fixture
def report_generator():
    """Provide a ReportGenerator instance for testing."""
    return ReportGenerator()

def test_display_console(report_generator, analysis_results, capsys):
    """Test console display with custom columns."""
    preferences = {'console_columns': ['ticker', 'score']}
    report_generator.display_console(analysis_results, preferences)
    captured = capsys.readouterr()
    expected_output = (
        "+----------+---------+\n"
        "| ticker   |   score |\n"
        "|----------+---------|\n"
        "| AAPL     |     1.5 |\n"
        "| MSFT     |     1.2 |\n"
        "| JNJ      |     1.1 |\n"
        "+----------+---------+"
    )
    assert expected_output in captured.out

def test_generate_csv_without_grouping(report_generator, analysis_results, tmp_path):
    """Test CSV generation without sector grouping."""
    preferences = {'csv_columns': ['ticker', 'sector', 'score'], 'group_by_sector': False}
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    report_generator.generate_csv(analysis_results, preferences, str(output_dir))
    csv_file = output_dir / "all_stocks.csv"
    assert csv_file.exists()
    df = pd.read_csv(csv_file)
    assert list(df.columns) == ['ticker', 'sector', 'score']
    assert len(df) == 3

def test_generate_csv_with_grouping(report_generator, analysis_results, tmp_path):
    """Test CSV generation with sector grouping."""
    preferences = {'csv_columns': ['ticker', 'sector', 'score'], 'group_by_sector': True}
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    report_generator.generate_csv(analysis_results, preferences, str(output_dir))
    tech_csv = output_dir / "Technology.csv"
    health_csv = output_dir / "Healthcare.csv"
    assert tech_csv.exists()
    assert health_csv.exists()
    tech_df = pd.read_csv(tech_csv)
    health_df = pd.read_csv(health_csv)
    assert len(tech_df) == 2
    assert len(health_df) == 1

def test_summarize_metrics_default(report_generator, analysis_results, capsys):
    """Test default metric summarization."""
    preferences = {'summary_metrics': ['count', 'average_score']}
    report_generator.summarize_metrics(analysis_results, preferences)
    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.split('\n') if line.strip()]
    assert any("Healthcare" in line and "1" in line and "1.10" in line for line in lines)
    assert any("Technology" in line and "2" in line and "1.35" in line for line in lines)

def test_summarize_metrics_custom(report_generator, analysis_results, capsys):
    """Test custom metric summarization."""
    preferences = {'summary_metrics': ['count', 'average_price', 'max_score']}
    report_generator.summarize_metrics(analysis_results, preferences)
    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.split('\n') if line.strip()]
    assert any("Healthcare" in line and "1" in line and "160.0" in line and "1.1" in line for line in lines)
    assert any("Technology" in line and "2" in line and "175.0" in line and "1.5" in line for line in lines)