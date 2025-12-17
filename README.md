# BlueSentra-AI
Agentless, behavior-based IoT anomaly detection with explainable triage for homes and small businesses.

BlueSentra AI is an early-stage security platform focused on identifying anomalous behavior across unmanaged IoT devices. The system emphasizes behavior-based detection rather than signatures, with clear explanations for why activity is flagged — enabling faster triage and trust in alerts.

---

## Problem

Homes and small businesses increasingly rely on IoT devices (cameras, routers, smart plugs, sensors) that lack centralized security controls. These devices are often unmanaged, rarely patched, and invisible to traditional endpoint or network security tools.

Existing solutions either:

- Require intrusive agents that IoT devices cannot support, or
- Generate alerts without clear explanations, increasing noise and fatigue.

---

## Solution

BlueSentra AI takes an **agentless, behavior-first approach**:

- Establishes baseline behavior for IoT devices
- Detects deviations in activity patterns
- Provides explainable context for why an alert was generated

The MVP validates that meaningful anomaly detection and triage can be achieved without agents, starting in smart home environments and extending naturally to SMB use cases.

---

## Architecture (MVP)

- **Dashboard:** Dash-based UI for visualizing device behavior and alerts
- **Core Logic:** Feature extraction, baseline modeling, anomaly detection, and explanations
- **Data Layer:** Simulated IoT telemetry for MVP validation
- **Future Edge Layer:** Raspberry Pi–based collectors for real device telemetry
