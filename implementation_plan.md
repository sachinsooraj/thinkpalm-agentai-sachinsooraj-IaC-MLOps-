# Implementation Plan - AI-Assisted IaC & MLOps Monitoring

This plan outlines the design and implementation of an end-to-end MLOps and Infrastructure-as-Code (IaC) demonstration. We will simulate an AI-assisted workflow where an initial Terraform config is generated, audited, and corrected to production standards, followed by a Python-based MLOps monitor that evaluates model endpoint performance (latency and data drift).

## User Review Required

> [!NOTE]
> We will use AWS S3 as the target cloud resource in the Terraform configuration, configuring it with production-grade security defaults (versioning, server-side encryption, and public access blocks).
> For the MLOps monitoring stub, we will implement a Python script that calculates both **latency** and **data drift** (using Population Stability Index or Kolmogorov-Smirnov test) on simulated model endpoint predictions, displaying the results in a beautiful, interactive `rich`-powered terminal interface.

## Proposed Changes

We will create a structured set of files in the `/home/thinkpalm/git-projects/training/mlops` workspace directory:

### Terraform & Prompt Doc

#### [NEW] [prompt_doc.md](file:///home/thinkpalm/git-projects/training/mlops/prompt_doc.md)
- Contains the prompt used to generate the initial Terraform file, the raw "before" code, a detailed before/after diff, and a breakdown of what the AI did well versus what required manual correction.

#### [NEW] [main.tf](file:///home/thinkpalm/git-projects/training/mlops/main.tf)
- The finalized, production-ready Terraform configuration for an AWS S3 bucket (hosting MLOps model artifacts).

### Python MLOps Monitor

#### [NEW] [model_monitor.py](file:///home/thinkpalm/git-projects/training/mlops/model_monitor.py)
- A Python monitoring stub that:
  - Generates realistic baseline and serving data (with mock drift injection).
  - Simulates model serving requests to log response latencies.
  - Computes data drift using the **Population Stability Index (PSI)** or **Kolmogorov-Smirnov (KS) Test** on prediction outputs.
  - Formats logs and status tables with stunning visual aesthetics using the `rich` Python library.

## Verification Plan

### Automated/Execution Tests
1. **Terraform Validation**:
   - Run `terraform init` and `terraform validate` to ensure the corrected `main.tf` has no syntax or configuration errors.
2. **Monitoring Stub Execution**:
   - Run `python model_monitor.py` to simulate real-time model requests, showing latency alerts and drift detection in action.

### Manual Verification & Visual Deliverables
- We will capture a beautiful screenshot of the `rich` console terminal output showcasing the alerts, metric tables, and active monitoring state.
