#!/usr/bin/env python3
"""
Comprehensive test coverage analysis and reporting tool.
Analyzes coverage data from multiple test suites and generates detailed reports.
"""
import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import tempfile


@dataclass
class CoverageMetrics:
    """Coverage metrics for a component or file."""
    lines_total: int
    lines_covered: int
    branches_total: int
    branches_covered: int
    functions_total: int
    functions_covered: int
    
    @property
    def line_coverage(self) -> float:
        """Calculate line coverage percentage."""
        return (self.lines_covered / self.lines_total * 100) if self.lines_total > 0 else 0
    
    @property
    def branch_coverage(self) -> float:
        """Calculate branch coverage percentage."""
        return (self.branches_covered / self.branches_total * 100) if self.branches_total > 0 else 0
    
    @property
    def function_coverage(self) -> float:
        """Calculate function coverage percentage."""
        return (self.functions_covered / self.functions_total * 100) if self.functions_total > 0 else 0


@dataclass
class ComponentCoverage:
    """Coverage data for a component (backend, frontend, etc.)."""
    name: str
    metrics: CoverageMetrics
    files: Dict[str, CoverageMetrics]
    uncovered_lines: Dict[str, List[int]]
    test_types: Dict[str, CoverageMetrics]  # unit, integration, e2e


@dataclass
class CoverageReport:
    """Complete coverage report."""
    timestamp: str
    overall_metrics: CoverageMetrics
    components: Dict[str, ComponentCoverage]
    trends: Optional[Dict[str, Any]] = None
    recommendations: List[str] = None


class CoverageAnalyzer:
    """Analyzes test coverage from multiple sources."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.coverage_dir = self.project_root / "coverage"
        self.reports_dir = self.project_root / "test-results" / "coverage"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_python_coverage(self) -> ComponentCoverage:
        """Analyze Python backend coverage from coverage.xml."""
        coverage_xml = self.project_root / "coverage.xml"
        
        if not coverage_xml.exists():
            print("Warning: coverage.xml not found. Running coverage analysis...")
            self._generate_python_coverage()
        
        if not coverage_xml.exists():
            print("Error: Could not generate Python coverage data")
            return self._empty_component_coverage("backend")
        
        # Parse coverage.xml
        tree = ET.parse(coverage_xml)
        root = tree.getroot()
        
        # Extract overall metrics
        coverage_elem = root.find(".//coverage")
        if coverage_elem is not None:
            lines_covered = int(coverage_elem.get("lines-covered", 0))
            lines_valid = int(coverage_elem.get("lines-valid", 0))
            branches_covered = int(coverage_elem.get("branches-covered", 0))
            branches_valid = int(coverage_elem.get("branches-valid", 0))
        else:
            lines_covered = lines_valid = branches_covered = branches_valid = 0
        
        overall_metrics = CoverageMetrics(
            lines_total=lines_valid,
            lines_covered=lines_covered,
            branches_total=branches_valid,
            branches_covered=branches_covered,
            functions_total=0,  # Not available in coverage.xml
            functions_covered=0
        )
        
        # Extract file-level metrics
        files = {}
        uncovered_lines = {}
        
        for package in root.findall(".//package"):
            for class_elem in package.findall(".//class"):
                filename = class_elem.get("filename", "")
                if not filename:
                    continue
                
                lines = class_elem.findall(".//line")
                total_lines = len(lines)
                covered_lines = len([l for l in lines if int(l.get("hits", 0)) > 0])
                
                # Extract uncovered line numbers
                uncovered = [
                    int(l.get("number", 0)) 
                    for l in lines 
                    if int(l.get("hits", 0)) == 0
                ]
                
                files[filename] = CoverageMetrics(
                    lines_total=total_lines,
                    lines_covered=covered_lines,
                    branches_total=0,  # Would need branch info
                    branches_covered=0,
                    functions_total=0,
                    functions_covered=0
                )
                
                if uncovered:
                    uncovered_lines[filename] = uncovered
        
        # Analyze by test type (would need separate coverage runs)
        test_types = {
            "unit": overall_metrics,  # Simplified for now
            "integration": self._empty_metrics(),
            "e2e": self._empty_metrics()
        }
        
        return ComponentCoverage(
            name="backend",
            metrics=overall_metrics,
            files=files,
            uncovered_lines=uncovered_lines,
            test_types=test_types
        )
    
    def analyze_frontend_coverage(self) -> ComponentCoverage:
        """Analyze frontend coverage from Jest coverage reports."""
        frontend_coverage = self.project_root / "frontend" / "coverage"
        coverage_summary = frontend_coverage / "coverage-summary.json"
        
        if not coverage_summary.exists():
            print("Warning: Frontend coverage not found. Running Jest coverage...")
            self._generate_frontend_coverage()
        
        if not coverage_summary.exists():
            print("Error: Could not generate frontend coverage data")
            return self._empty_component_coverage("frontend")
        
        # Parse coverage-summary.json
        with open(coverage_summary) as f:
            coverage_data = json.load(f)
        
        total = coverage_data.get("total", {})
        
        overall_metrics = CoverageMetrics(
            lines_total=total.get("lines", {}).get("total", 0),
            lines_covered=total.get("lines", {}).get("covered", 0),
            branches_total=total.get("branches", {}).get("total", 0),
            branches_covered=total.get("branches", {}).get("covered", 0),
            functions_total=total.get("functions", {}).get("total", 0),
            functions_covered=total.get("functions", {}).get("covered", 0)
        )
        
        # Extract file-level metrics
        files = {}
        uncovered_lines = {}
        
        for filepath, file_data in coverage_data.items():
            if filepath == "total":
                continue
            
            files[filepath] = CoverageMetrics(
                lines_total=file_data.get("lines", {}).get("total", 0),
                lines_covered=file_data.get("lines", {}).get("covered", 0),
                branches_total=file_data.get("branches", {}).get("total", 0),
                branches_covered=file_data.get("branches", {}).get("covered", 0),
                functions_total=file_data.get("functions", {}).get("total", 0),
                functions_covered=file_data.get("functions", {}).get("covered", 0)
            )
            
            # Extract uncovered lines (would need detailed coverage data)
            uncovered = file_data.get("lines", {}).get("uncovered", [])
            if uncovered:
                uncovered_lines[filepath] = uncovered
        
        test_types = {
            "unit": overall_metrics,
            "integration": self._empty_metrics(),
            "e2e": self._empty_metrics()
        }
        
        return ComponentCoverage(
            name="frontend",
            metrics=overall_metrics,
            files=files,
            uncovered_lines=uncovered_lines,
            test_types=test_types
        )
    
    def analyze_e2e_coverage(self) -> ComponentCoverage:
        """Analyze E2E test coverage from Playwright."""
        # E2E coverage would be collected differently
        # For now, return empty coverage
        return self._empty_component_coverage("e2e")
    
    def generate_comprehensive_report(self) -> CoverageReport:
        """Generate comprehensive coverage report."""
        print("Generating comprehensive coverage report...")
        
        # Analyze all components
        backend_coverage = self.analyze_python_coverage()
        frontend_coverage = self.analyze_frontend_coverage()
        e2e_coverage = self.analyze_e2e_coverage()
        
        components = {
            "backend": backend_coverage,
            "frontend": frontend_coverage,
            "e2e": e2e_coverage
        }
        
        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics(components)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(components)
        
        # Load trends if available
        trends = self._load_coverage_trends()
        
        report = CoverageReport(
            timestamp=datetime.now().isoformat(),
            overall_metrics=overall_metrics,
            components=components,
            trends=trends,
            recommendations=recommendations
        )
        
        return report
    
    def export_report(self, report: CoverageReport, format: str = "all"):
        """Export coverage report in various formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format in ["json", "all"]:
            self._export_json_report(report, f"coverage_report_{timestamp}.json")
        
        if format in ["html", "all"]:
            self._export_html_report(report, f"coverage_report_{timestamp}.html")
        
        if format in ["csv", "all"]:
            self._export_csv_report(report, f"coverage_report_{timestamp}.csv")
        
        if format in ["markdown", "all"]:
            self._export_markdown_report(report, f"coverage_report_{timestamp}.md")
    
    def _generate_python_coverage(self):
        """Generate Python coverage data."""
        try:
            # Run pytest with coverage
            subprocess.run([
                "python", "-m", "pytest",
                "tests/",
                "--cov=src/app",
                "--cov-report=xml",
                "--cov-report=html",
                "--cov-report=term-missing"
            ], cwd=self.project_root, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error generating Python coverage: {e}")
    
    def _generate_frontend_coverage(self):
        """Generate frontend coverage data."""
        try:
            # Run Jest with coverage
            subprocess.run([
                "npm", "run", "test:coverage"
            ], cwd=self.project_root / "frontend", check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error generating frontend coverage: {e}")
    
    def _empty_component_coverage(self, name: str) -> ComponentCoverage:
        """Create empty component coverage."""
        return ComponentCoverage(
            name=name,
            metrics=self._empty_metrics(),
            files={},
            uncovered_lines={},
            test_types={}
        )
    
    def _empty_metrics(self) -> CoverageMetrics:
        """Create empty coverage metrics."""
        return CoverageMetrics(0, 0, 0, 0, 0, 0)
    
    def _calculate_overall_metrics(self, components: Dict[str, ComponentCoverage]) -> CoverageMetrics:
        """Calculate overall metrics from all components."""
        total_lines = sum(c.metrics.lines_total for c in components.values())
        covered_lines = sum(c.metrics.lines_covered for c in components.values())
        total_branches = sum(c.metrics.branches_total for c in components.values())
        covered_branches = sum(c.metrics.branches_covered for c in components.values())
        total_functions = sum(c.metrics.functions_total for c in components.values())
        covered_functions = sum(c.metrics.functions_covered for c in components.values())
        
        return CoverageMetrics(
            lines_total=total_lines,
            lines_covered=covered_lines,
            branches_total=total_branches,
            branches_covered=covered_branches,
            functions_total=total_functions,
            functions_covered=covered_functions
        )
    
    def _generate_recommendations(self, components: Dict[str, ComponentCoverage]) -> List[str]:
        """Generate coverage improvement recommendations."""
        recommendations = []
        
        for name, component in components.items():
            metrics = component.metrics
            
            if metrics.line_coverage < 80:
                recommendations.append(
                    f"{name.title()}: Line coverage ({metrics.line_coverage:.1f}%) "
                    f"is below 80% target. Add {metrics.lines_total - metrics.lines_covered} "
                    f"more covered lines."
                )
            
            if metrics.branch_coverage < 70:
                recommendations.append(
                    f"{name.title()}: Branch coverage ({metrics.branch_coverage:.1f}%) "
                    f"is below 70% target. Add tests for edge cases and error conditions."
                )
            
            if metrics.function_coverage < 90:
                recommendations.append(
                    f"{name.title()}: Function coverage ({metrics.function_coverage:.1f}%) "
                    f"is below 90% target. Add {metrics.functions_total - metrics.functions_covered} "
                    f"more function tests."
                )
            
            # Identify files with low coverage
            low_coverage_files = [
                filepath for filepath, file_metrics in component.files.items()
                if file_metrics.line_coverage < 60
            ]
            
            if low_coverage_files:
                recommendations.append(
                    f"{name.title()}: Files with low coverage (< 60%): " +
                    ", ".join(low_coverage_files[:5]) +
                    ("..." if len(low_coverage_files) > 5 else "")
                )
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Great job! All components meet coverage targets.")
        else:
            recommendations.append(
                "Consider adding integration tests to improve cross-component coverage."
            )
            recommendations.append(
                "Use mutation testing to verify test quality beyond coverage metrics."
            )
        
        return recommendations
    
    def _load_coverage_trends(self) -> Optional[Dict[str, Any]]:
        """Load historical coverage trends."""
        trends_file = self.reports_dir / "coverage_trends.json"
        
        if trends_file.exists():
            try:
                with open(trends_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return None
    
    def _export_json_report(self, report: CoverageReport, filename: str):
        """Export report as JSON."""
        output_file = self.reports_dir / filename
        
        # Convert dataclasses to dict
        report_dict = asdict(report)
        
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        print(f"JSON report exported to: {output_file}")
    
    def _export_html_report(self, report: CoverageReport, filename: str):
        """Export report as HTML."""
        output_file = self.reports_dir / filename
        
        html_content = self._generate_html_content(report)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report exported to: {output_file}")
    
    def _export_csv_report(self, report: CoverageReport, filename: str):
        """Export report as CSV."""
        output_file = self.reports_dir / filename
        
        import csv
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Component", "File", "Lines Total", "Lines Covered", "Line Coverage %",
                "Branches Total", "Branches Covered", "Branch Coverage %",
                "Functions Total", "Functions Covered", "Function Coverage %"
            ])
            
            # Data rows
            for component_name, component in report.components.items():
                # Component summary
                metrics = component.metrics
                writer.writerow([
                    component_name, "TOTAL",
                    metrics.lines_total, metrics.lines_covered, f"{metrics.line_coverage:.1f}",
                    metrics.branches_total, metrics.branches_covered, f"{metrics.branch_coverage:.1f}",
                    metrics.functions_total, metrics.functions_covered, f"{metrics.function_coverage:.1f}"
                ])
                
                # File details
                for filepath, file_metrics in component.files.items():
                    writer.writerow([
                        component_name, filepath,
                        file_metrics.lines_total, file_metrics.lines_covered, f"{file_metrics.line_coverage:.1f}",
                        file_metrics.branches_total, file_metrics.branches_covered, f"{file_metrics.branch_coverage:.1f}",
                        file_metrics.functions_total, file_metrics.functions_covered, f"{file_metrics.function_coverage:.1f}"
                    ])
        
        print(f"CSV report exported to: {output_file}")
    
    def _export_markdown_report(self, report: CoverageReport, filename: str):
        """Export report as Markdown."""
        output_file = self.reports_dir / filename
        
        md_content = self._generate_markdown_content(report)
        
        with open(output_file, 'w') as f:
            f.write(md_content)
        
        print(f"Markdown report exported to: {output_file}")
    
    def _generate_html_content(self, report: CoverageReport) -> str:
        """Generate HTML content for the report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Coverage Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metric-card {{ background: white; border: 1px solid #dee2e6; padding: 15px; border-radius: 8px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; }}
        .coverage-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .coverage-fill {{ height: 100%; transition: width 0.3s ease; }}
        .good {{ background: #28a745; }}
        .warning {{ background: #ffc107; }}
        .danger {{ background: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; }}
        .component-section {{ margin: 30px 0; }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Coverage Report</h1>
        <p>Generated: {report.timestamp}</p>
    </div>
    
    <div class="metrics">
        {self._generate_metric_card("Overall Line Coverage", report.overall_metrics.line_coverage)}
        {self._generate_metric_card("Overall Branch Coverage", report.overall_metrics.branch_coverage)}
        {self._generate_metric_card("Overall Function Coverage", report.overall_metrics.function_coverage)}
    </div>
    
    {self._generate_component_sections_html(report.components)}
    
    <div class="recommendations">
        <h3>Recommendations</h3>
        <ul>
            {"".join(f"<li>{rec}</li>" for rec in report.recommendations or [])}
        </ul>
    </div>
</body>
</html>
        """
        return html
    
    def _generate_metric_card(self, title: str, value: float) -> str:
        """Generate HTML for a metric card."""
        css_class = "good" if value >= 80 else "warning" if value >= 60 else "danger"
        
        return f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <div class="metric-value">{value:.1f}%</div>
            <div class="coverage-bar">
                <div class="coverage-fill {css_class}" style="width: {value}%"></div>
            </div>
        </div>
        """
    
    def _generate_component_sections_html(self, components: Dict[str, ComponentCoverage]) -> str:
        """Generate HTML for component sections."""
        sections = []
        
        for name, component in components.items():
            if component.metrics.lines_total == 0:
                continue
            
            section = f"""
            <div class="component-section">
                <h2>{name.title()} Coverage</h2>
                <div class="metrics">
                    {self._generate_metric_card(f"{name} Line Coverage", component.metrics.line_coverage)}
                    {self._generate_metric_card(f"{name} Branch Coverage", component.metrics.branch_coverage)}
                    {self._generate_metric_card(f"{name} Function Coverage", component.metrics.function_coverage)}
                </div>
                
                <h3>File Coverage Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>File</th>
                            <th>Lines</th>
                            <th>Branches</th>
                            <th>Functions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_file_rows_html(component.files)}
                    </tbody>
                </table>
            </div>
            """
            sections.append(section)
        
        return "".join(sections)
    
    def _generate_file_rows_html(self, files: Dict[str, CoverageMetrics]) -> str:
        """Generate HTML for file coverage rows."""
        rows = []
        
        for filepath, metrics in files.items():
            row = f"""
            <tr>
                <td>{filepath}</td>
                <td>{metrics.line_coverage:.1f}% ({metrics.lines_covered}/{metrics.lines_total})</td>
                <td>{metrics.branch_coverage:.1f}% ({metrics.branches_covered}/{metrics.branches_total})</td>
                <td>{metrics.function_coverage:.1f}% ({metrics.functions_covered}/{metrics.functions_total})</td>
            </tr>
            """
            rows.append(row)
        
        return "".join(rows)
    
    def _generate_markdown_content(self, report: CoverageReport) -> str:
        """Generate Markdown content for the report."""
        md = f"""# Test Coverage Report

Generated: {report.timestamp}

## Overall Coverage

| Metric | Coverage |
|--------|----------|
| Lines | {report.overall_metrics.line_coverage:.1f}% ({report.overall_metrics.lines_covered}/{report.overall_metrics.lines_total}) |
| Branches | {report.overall_metrics.branch_coverage:.1f}% ({report.overall_metrics.branches_covered}/{report.overall_metrics.branches_total}) |
| Functions | {report.overall_metrics.function_coverage:.1f}% ({report.overall_metrics.functions_covered}/{report.overall_metrics.functions_total}) |

"""
        
        # Component sections
        for name, component in report.components.items():
            if component.metrics.lines_total == 0:
                continue
            
            md += f"""## {name.title()} Coverage

| Metric | Coverage |
|--------|----------|
| Lines | {component.metrics.line_coverage:.1f}% ({component.metrics.lines_covered}/{component.metrics.lines_total}) |
| Branches | {component.metrics.branch_coverage:.1f}% ({component.metrics.branches_covered}/{component.metrics.branches_total}) |
| Functions | {component.metrics.function_coverage:.1f}% ({component.metrics.functions_covered}/{component.metrics.functions_total}) |

### File Details

| File | Line Coverage | Branch Coverage | Function Coverage |
|------|---------------|-----------------|-------------------|
"""
            
            for filepath, metrics in component.files.items():
                md += f"| {filepath} | {metrics.line_coverage:.1f}% | {metrics.branch_coverage:.1f}% | {metrics.function_coverage:.1f}% |\n"
            
            md += "\n"
        
        # Recommendations
        if report.recommendations:
            md += "## Recommendations\n\n"
            for rec in report.recommendations:
                md += f"- {rec}\n"
        
        return md


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze test coverage")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--format", choices=["json", "html", "csv", "markdown", "all"], 
                       default="all", help="Output format")
    parser.add_argument("--generate", action="store_true", 
                       help="Generate fresh coverage data before analysis")
    
    args = parser.parse_args()
    
    analyzer = CoverageAnalyzer(args.project_root)
    
    if args.generate:
        print("Generating fresh coverage data...")
        analyzer._generate_python_coverage()
        analyzer._generate_frontend_coverage()
    
    report = analyzer.generate_comprehensive_report()
    analyzer.export_report(report, args.format)
    
    # Print summary to console
    print(f"\n=== Coverage Summary ===")
    print(f"Overall Line Coverage: {report.overall_metrics.line_coverage:.1f}%")
    print(f"Overall Branch Coverage: {report.overall_metrics.branch_coverage:.1f}%")
    print(f"Overall Function Coverage: {report.overall_metrics.function_coverage:.1f}%")
    
    for name, component in report.components.items():
        if component.metrics.lines_total > 0:
            print(f"{name.title()}: {component.metrics.line_coverage:.1f}% lines, "
                  f"{component.metrics.branch_coverage:.1f}% branches")
    
    if report.recommendations:
        print(f"\n=== Recommendations ===")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main()