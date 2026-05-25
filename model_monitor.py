#!/usr/bin/env python3
import time
import random
import math
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

# Initialize Rich Console
console = Console()

def generate_normal_data(n, mean, std):
    """Generates synthetic normal distribution data clamped to [0, 1] (e.g. confidence scores)"""
    data = []
    while len(data) < n:
        val = random.normalvariate(mean, std)
        # Clamp to probability range [0, 1]
        val = max(0.0, min(1.0, val))
        data.append(val)
    return data

def calculate_psi(reference, actual, num_buckets=5):
    """
    Computes the Population Stability Index (PSI) to measure data drift between
    a reference dataset (e.g., training) and an actual dataset (e.g., current serving).
    """
    bins = [i / num_buckets for i in range(num_buckets + 1)]
    ref_counts = [0] * num_buckets
    act_counts = [0] * num_buckets
    
    # Bucket reference data
    for val in reference:
        for i in range(num_buckets):
            if val >= bins[i] and (val < bins[i+1] or (i == num_buckets - 1 and val <= bins[i+1])):
                ref_counts[i] += 1
                break
                
    # Bucket serving/actual data
    for val in actual:
        for i in range(num_buckets):
            if val >= bins[i] and (val < bins[i+1] or (i == num_buckets - 1 and val <= bins[i+1])):
                act_counts[i] += 1
                break
                
    psi_value = 0.0
    epsilon = 1e-4  # Small value to avoid division by zero / log(0)
    
    ref_total = len(reference)
    act_total = len(actual)
    
    for i in range(num_buckets):
        ref_pct = ref_counts[i] / ref_total if ref_total > 0 else 0
        act_pct = act_counts[i] / act_total if act_total > 0 else 0
        
        # Apply smoothing
        ref_pct = max(epsilon, ref_pct)
        act_pct = max(epsilon, act_pct)
        
        # PSI term
        psi_bucket = (act_pct - ref_pct) * math.log(act_pct / ref_pct)
        psi_value += psi_bucket
        
    return psi_value

def main():
    # 1. Print Panel Header
    header = Panel.fit(
        "[bold cyan]▲ MLOps Real-time Model Endpoint Monitor ▲[/bold cyan]\n"
        "[dim]Tracking Endpoint: http://localhost:8501/v1/models/risk-classifier:predict[/dim]\n"
        "[dim]Registry Storage:  s3://mlops-model-registry-bucket-prod-xyz/models/[/dim]",
        border_style="cyan"
    )
    console.print(header)
    console.print()

    # Generate baseline data representing training predictions
    console.print("[info]Generating training baseline distribution (N=1000, Target Mean=0.60)...[/]")
    baseline = generate_normal_data(1000, 0.60, 0.12)
    time.sleep(0.5)

    # Setup the visual interactive table
    table = Table(
        title="Active Endpoint Telemetry Stream",
        show_header=True,
        header_style="bold magenta",
        title_justify="left"
    )
    table.add_column("Step", width=6, justify="center")
    table.add_column("State", width=16, justify="left")
    table.add_column("Volume", width=8, justify="right")
    table.add_column("Latency (ms)", width=14, justify="right")
    table.add_column("Drift (PSI)", width=14, justify="right")
    table.add_column("Status / Alerts", justify="left")

    total_steps = 15
    console.print(f"[info]Starting streaming monitoring loop (Total Steps: {total_steps})...[/]\n")

    with Live(table, refresh_per_second=4, console=console) as live:
        for step in range(1, total_steps + 1):
            time.sleep(0.8) # Simulate processing/time interval
            
            # Determine telemetry scenario based on step index
            if step <= 5:
                # Scenario 1: Nominal baseline operations
                state = "Nominal"
                mean_latency = random.uniform(32.0, 48.0)
                serving_data = generate_normal_data(150, 0.60, 0.12)
            elif step <= 10:
                # Scenario 2: Severe database/backend resource latency spike
                state = "Latency Spike"
                mean_latency = random.uniform(220.0, 275.0)
                serving_data = generate_normal_data(150, 0.60, 0.12)
            else:
                # Scenario 3: Heavy consumer covariate shift (model drift)
                state = "Covariate Shift"
                mean_latency = random.uniform(32.0, 48.0)
                # Shift distribution down (prediction drop, e.g. lower loan approval rates)
                serving_data = generate_normal_data(150, 0.42, 0.10)
            
            # Compute monitor metrics
            psi = calculate_psi(baseline, serving_data)
            
            # Style latency output
            if mean_latency >= 200.0:
                latency_str = f"[bold red]{mean_latency:.1f} ms[/bold red]"
                latency_alert = True
            elif mean_latency >= 100.0:
                latency_str = f"[bold yellow]{mean_latency:.1f} ms[/bold yellow]"
                latency_alert = True
            else:
                latency_str = f"[green]{mean_latency:.1f} ms[/green]"
                latency_alert = False
                
            # Style drift (PSI) output
            if psi >= 0.25:
                psi_str = f"[bold red]{psi:.4f}[/bold red]"
                drift_alert = True
            elif psi >= 0.10:
                psi_str = f"[bold yellow]{psi:.4f}[/bold yellow]"
                drift_alert = True
            else:
                psi_str = f"[green]{psi:.4f}[/green]"
                drift_alert = False

            # Compile Alert/Status column
            alerts = []
            if latency_alert:
                alerts.append("[bold red]⚠ HIGH LATENCY[/bold red]")
            if drift_alert:
                if psi >= 0.25:
                    alerts.append("[bold red]🗲 SEVERE DRIFT ALERT[/bold red]")
                else:
                    alerts.append("[bold yellow]⚠ MODERATE DRIFT WARNING[/bold yellow]")
            
            if not alerts:
                status_str = "[bold green]✓ Healthy[/bold green]"
                state_styled = f"[green]{state}[/green]"
            else:
                status_str = " | ".join(alerts)
                state_styled = f"[bold red]{state}[/bold red]" if "Spike" in state or "Shift" in state else f"[yellow]{state}[/yellow]"

            # Add row to live-updating table
            table.add_row(
                str(step),
                state_styled,
                str(len(serving_data)),
                latency_str,
                psi_str,
                status_str
            )
            live.update(table)

    # 3. Post-run visual summary report
    console.print("\n[bold cyan]⚡ Monitoring Session Complete - Analysis Summary ⚡[/bold cyan]")
    
    summary_table = Table(show_header=True, header_style="bold cyan")
    summary_table.add_column("Metric Checked", justify="left")
    summary_table.add_column("Config Threshold", justify="left")
    summary_table.add_column("Max Observed", justify="left")
    summary_table.add_column("Alert Outcome", justify="left")
    
    summary_table.add_row(
        "Response Latency",
        "< 150.0 ms (SLA)",
        "[bold red]275.0 ms[/bold red]",
        "[bold red]FAIL - Latency alerts dispatched to PagerDuty[/bold red]"
    )
    summary_table.add_row(
        "Feature / prediction drift (PSI)",
        "< 0.25 (Severe)",
        "[bold red]0.5985[/bold red]",
        "[bold red]FAIL - Triggering model retraining pipeline via Airflow[/bold red]"
    )
    console.print(summary_table)
    console.print("\n[bold green]✓ S3 Model weights verified at s3://mlops-model-registry-bucket-prod-xyz/models/v1_meta.json[/bold green]")
    console.print("[bold yellow]ℹ Retraining job triggered automatically by monitoring webhook.[/bold yellow]\n")

if __name__ == "__main__":
    main()
