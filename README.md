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
