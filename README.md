# 🚦 DQN Based Traffic Optimization

An intelligent traffic signal control system built using **SUMO (Simulation of Urban Mobility)** and **Deep Reinforcement Learning (DQN)**.  
The system dynamically optimizes traffic signal timings to reduce congestion and waiting time, with **special priority handling for emergency vehicles** and a **real-time Streamlit dashboard**.

---

## 📌 Overview

This project simulates an urban traffic intersection and controls traffic signals using two approaches:
- **Rule-based traffic signal control**
- **AI-based control using Deep Q-Network (DQN)**

The goal is to improve traffic flow efficiency by minimizing vehicle waiting time and congestion.  
A **real-time dashboard** allows users to monitor traffic performance, emergency vehicle movement, and AI training progress.

---

## ✨ Key Features

### 🚦 Traffic Signal Control
- Rule-based traffic light controller
- DQN-based adaptive traffic signal controller
- Dynamic signal phase switching
- Starvation prevention for long-waiting lanes

### 🚨 Emergency Vehicle Priority
- Priority handling for emergency vehicles
- Immediate green signal for emergency routes
- Supports ambulance, police, and fire truck
- Realistic speed and behavior configuration

### 📊 Real-Time Dashboard
- Live traffic statistics
- Emergency vehicle tracking
- AI training metrics visualization
- Auto-refresh every 2 seconds

---

## 🧠 AI & Simulation Details

- **Reinforcement Learning Algorithm**: Deep Q-Network (DQN)
- **State Space**:
  - Lane queue lengths
  - Vehicle count
  - Average waiting time
- **Actions**:
  - Traffic signal phase switching
- **Reward Function**:
  - Reduces waiting time and congestion
- **Simulation Step Length**: 0.1 seconds for smooth vehicle movement

---

## 🏗️ System Architecture

The project follows a **three-layer architecture**:

### 1️⃣ SUMO Simulation Engine
- Handles traffic flow and vehicle movement
- Communicates using TraCI (Traffic Control Interface)

### 2️⃣ Traffic Control Layer
- Rule-based controller
- DQN-based reinforcement learning controller
- Makes real-time traffic signal decisions

### 3️⃣ Streamlit Dashboard
- Web-based monitoring interface
- Displays real-time traffic metrics
- Controls simulation mode and execution

The simulation and dashboard communicate using JSON-based metric files to keep the system simple and reliable.

## Project Structure

```
.
├── run.py                      # Main simulation entry point
├── start_application.py        # Application launcher (dashboard + simulation)
├── config/
│   ├── traffic_controller.py  # Abstract base controller
│   ├── rule_based_controller.py # Rule-based control implementation
│   └── dqn_agent.py           # Deep Q-Network RL agent
├── network/
│   ├── generate_network.py    # 3x3 grid network generator
│   ├── vehicle_types.py       # Vehicle type definitions
│   ├── route_generator.py     # Dynamic route generation (FIXED)
│   └── urban_elements.py      # Buildings, trees, POIs
├── dashboard/
│   └── app.py                 # Streamlit dashboard application (FIXED)
├── models/                     # Saved DQN models
└── logs/                      # Simulation logs
```

## How to Run

### Quick Start (Dashboard Only)
```bash
python start_application.py
```
This starts the dashboard at http://localhost:5000. Use dashboard controls to start/stop simulation.

### With Simulation Auto-Start
```bash
# Rule-based mode with GUI
python start_application.py --auto-start --mode rule

# RL-based mode without GUI (faster)
python start_application.py --auto-start --mode rl --no-gui
```

### Direct Simulation (No Dashboard)
```bash
# Rule-based with GUI
python run.py --mode rule --gui

# RL training (headless)
python run.py --mode rl --no-gui
```

## Technical Notes

- **Port**: Dashboard runs on port 5000 (hardcoded, firewalled safe)
- **Default Mode**: Rule-based control (safer, more predictable)
- **Workflow**: `Dashboard` workflow automatically starts the application
- **Metrics Update**: Every 10 simulation steps (configurable)
- **RL Training**: Batch training every 50 steps when in RL mode
- **Step Length**: 0.1 seconds for smooth, realistic vehicle movement
- **Dashboard Refresh**: 2-second auto-refresh for real-time metric updates
