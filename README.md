# BlueSentra AI

**Agentless IoT Threat Detection for Outpatient Healthcare Environments**

BlueSentra AI is a behavior-based, agentless security platform designed to detect anomalous activity across unmanaged IoT devices in outpatient healthcare settings. The system focuses on network-level behavior rather than signatures or endpoint agents, enabling visibility into devices that traditional EDR and MDM solutions cannot cover.

---

## Problem

Outpatient clinics increasingly rely on unmanaged IoT devices—patient monitors, imaging peripherals, smart TVs, and legacy networked equipment—that operate outside traditional security controls. These devices expand the attack surface while lacking continuous behavioral monitoring.

---

## Solution

BlueSentra AI passively observes network behavior to:
- Establish device-level behavioral baselines
- Detect deviations indicative of compromise or misuse
- Provide explainable alerts without requiring agents or firmware changes

---

## MVP Status

✅ Behavior-based anomaly detection  
✅ Simulated IoT traffic generation  
✅ Explainable alerting pipeline  
🔄 Early-stage prototype (research + validation)

---

## Documentation

- 📄 **Research Paper:** `docs/BlueSentra_AI_Research_Paper.pdf`
- 🧠 Architecture overview included in `/docs`

---

## Tech Stack

- **Python**
- **Streamlit** (dashboard)
- **Pandas / NumPy**
- **Raspberry Pi (Edge Prototype)**
- **CSV-based alert pipeline (MVP)**

---

## License

MIT License © 2025 Jonathan Daniel Campbell

