# 🛡️ BlueSentra AI
## Agentless IoT Threat Detection for Outpatient Clinics & Small Healthcare Facilities

> **Passive, behavior-based security for unmanaged medical and IoT devices — without agents, credentials, or network changes.**

---

## 🚨 The Problem

Outpatient clinics and small healthcare facilities rely heavily on **unmanaged IoT and medical-adjacent devices** such as:

- Network printers  
- Imaging systems  
- Patient monitors  
- Security cameras  
- HVAC and building systems  

These devices:
- Cannot run endpoint agents  
- Are often invisible to traditional security tools  
- Introduce compliance and ransomware risk (HIPAA)  

Most small clinics lack a dedicated SOC or security team.

---

## ✅ The Solution

**BlueSentra AI** passively monitors network traffic to:

- 🔍 Discover unmanaged devices automatically  
- 📈 Establish normal behavioral baselines  
- 🚩 Detect anomalous or suspicious activity  
- 🧠 Deliver **explainable alerts** that non-expert teams can act on  

All without:
- ❌ Installing agents  
- ❌ Using device credentials  
- ❌ Reconfiguring the network  

---

## 🧠 Core Capabilities

### 🔍 Agentless Device Discovery
Identifies unmanaged devices based on observed network behavior.

### 📊 Behavioral Baseline Modeling
Learns normal communication patterns for each device over time.

### 🚩 Anomaly Detection
Flags deviations such as:
- Unexpected external destinations  
- Abnormal traffic volumes  
- Protocol misuse or timing changes  

### 🧠 Explainable Alerts
Each alert includes:
- What changed  
- Why it matters  
- When it occurred  

### 🖥️ Lightweight Edge Deployment
Designed to run on low-cost edge hardware (e.g., Raspberry Pi).

---

## 🏥 Target Environment

### Initial Focus
- Outpatient clinics  
- Small healthcare practices  
- Imaging centers  
- Specialty medical offices  

### Typical Characteristics
- 10–200 networked devices  
- No internal SOC  
- Managed by MSPs or small IT teams  

---

## 🏗️ MVP Architecture

[ Clinic Network Traffic ]
↓
[ Edge Sensor (Raspberry Pi) ]
↓
[ Feature Extraction & Baselines ]
↓
[ Anomaly Detection Engine ]
↓
[ Streamlit Dashboard & Alerts ]


> This MVP validates that **agentless, behavior-based detection** is feasible in real-world healthcare networks.

---

## 🧪 MVP Status

### ✅ Implemented
- Device behavior simulation  
- Baseline generation  
- Anomaly detection logic  
- Explainable alert output  
- Interactive dashboard (Streamlit)

### 🚧 Not Yet Implemented
- Live packet capture on production networks  
- Cloud backend  
- Production hardening  

> This repository represents a **proof-of-concept**, not a production security appliance.

---

## 🚀 Roadmap

### Near Term
- Controlled pilot deployments  
- Expanded device profiling  
- MSP-friendly reporting  

### Mid Term
- Multi-site visibility  
- Centralized management  
- Improved anomaly scoring  

### Long Term
- Healthcare-specific risk models  
- Compliance-oriented reporting  
- Commercial SaaS platform  

---

## 🤝 Intended Audience

- Managed Service Providers (MSPs) serving healthcare clients  
- Small healthcare IT teams  
- Security engineers evaluating IoT risk  
- Early-stage investors and partners  

---

## ⚠️ Disclaimer

BlueSentra AI is an experimental research project and **not intended for production use** in live healthcare environments without proper validation, approvals, and security review.

---

## 📌 Why BlueSentra AI Matters

Unmanaged IoT devices are one of the **least visible and fastest-growing attack surfaces** in healthcare.

BlueSentra AI explores how **agentless, behavior-based detection** can make this risk visible — without requiring enterprise-scale infrastructure.
