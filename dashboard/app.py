import streamlit as st
import json
import time
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import subprocess

st.set_page_config(
    page_title="Traffic Signal Control Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'simulation_process' not in st.session_state:
    st.session_state.simulation_process = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def load_metrics():
    """Load current simulation metrics"""
    try:
        if os.path.exists('dashboard/metrics.json'):
            with open('dashboard/metrics.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        'avg_waiting_time': 0.0,
        'total_vehicles': 0,
        'emergency_vehicles': 0,
        'regular_vehicles': 0,
        'queue_lengths': {},
        'emergency_vehicle_list': []
    }

def load_training_stats():
    """Load RL training statistics"""
    try:
        if os.path.exists('dashboard/training_stats.json'):
            with open('dashboard/training_stats.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {'rewards': [], 'epsilon': [], 'losses': []}

def save_control_mode(mode):
    """Save control mode to file"""
    os.makedirs('dashboard', exist_ok=True)
    with open('dashboard/control_mode.txt', 'w') as f:
        f.write(mode)

def load_control_mode():
    """Load current control mode"""
    try:
        if os.path.exists('dashboard/control_mode.txt'):
            with open('dashboard/control_mode.txt', 'r') as f:
                return f.read().strip()
    except:
        pass
    return 'Rule-based'

def start_simulation(mode, gui=True):
    """Start the traffic simulation"""
    if st.session_state.simulation_process is not None:
        try:
            st.session_state.simulation_process.terminate()
            st.session_state.simulation_process.wait(timeout=5)
        except:
            pass
    
    cmd = ['python', 'run.py', '--mode', mode]
    if gui:
        cmd.append('--gui')
    
    try:
        st.session_state.simulation_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        st.error(f"Failed to start simulation: {e}")
        return False

def stop_simulation():
    """Stop the running simulation"""
    if st.session_state.simulation_process is not None:
        try:
            st.session_state.simulation_process.terminate()
            st.session_state.simulation_process.wait(timeout=5)
            st.session_state.simulation_process = None
            return True
        except:
            try:
                st.session_state.simulation_process.kill()
                st.session_state.simulation_process = None
                return True
            except:
                pass
    return False

def is_simulation_running():
    """Check if simulation is currently running"""
    if st.session_state.simulation_process is None:
        return False
    return st.session_state.simulation_process.poll() is None

st.title("🚦 Traffic Signal Control Dashboard")
st.markdown("Real-time monitoring and control of traffic simulation")

with st.sidebar:
    st.header("🎛️ Control Panel")
    
    st.subheader("Simulation Control")
    
    current_mode = load_control_mode()
    control_mode = st.radio(
        "Control Mode:",
        options=["Rule-based", "RL-based"],
        index=0 if current_mode == "Rule-based" else 1,
        help="Choose between rule-based traffic control or reinforcement learning"
    )
    
    if control_mode != current_mode:
        save_control_mode(control_mode)
        st.success(f"Control mode changed to {control_mode}")
        time.sleep(0.5)
        st.rerun()
    
    st.divider()
    
    running = is_simulation_running()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start", disabled=running, use_container_width=True):
            mode = 'rl' if control_mode == 'RL-based' else 'rule'
            if start_simulation(mode, gui=True):
                st.success("Simulation started!")
                time.sleep(1)
                st.rerun()
    
    with col2:
        if st.button("⏹️ Stop", disabled=not running, use_container_width=True):
            if stop_simulation():
                st.success("Simulation stopped!")
                time.sleep(1)
                st.rerun()
    
    if running:
        st.success("🟢 Simulation Running")
    else:
        st.error("🔴 Simulation Stopped")
    
    st.divider()
    
    st.subheader("📊 Quick Stats")
    metrics = load_metrics()
    
    st.metric("Total Vehicles", metrics['total_vehicles'])
    st.metric("Emergency Vehicles", metrics.get('emergency_vehicles', 0))
    st.metric("Avg Wait Time", f"{metrics['avg_waiting_time']:.1f}s")

tab1, tab2, tab3 = st.tabs(["📈 Real-time Metrics", "🚨 Emergency Vehicles", "🧠 AI Training"])

with tab1:
    st.header("Real-time Traffic Metrics")
    
    if running:
        metrics = load_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Average Waiting Time",
                f"{metrics['avg_waiting_time']*100:.1f}s",
                delta=None
            )
        
        with col2:
            st.metric(
                "Total Vehicles",
                metrics['total_vehicles'],
                delta=None
            )
        
        with col3:
            emergency_count = metrics.get('emergency_vehicles', 0)
            st.metric(
                "Emergency Vehicles",
                emergency_count,
                delta=None
            )
        
        if metrics['queue_lengths']:
            st.subheader("Lane Queue Lengths")
            
            queue_data = metrics['queue_lengths']
            if queue_data:
                df = pd.DataFrame(list(queue_data.items()), columns=['Lane', 'Queue Length'])
                df = df[df['Queue Length'] > 0].sort_values('Queue Length', ascending=False)
                
                if not df.empty:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    bars = ax.bar(df['Lane'], df['Queue Length'], color='#FF6B6B')
                    ax.set_xlabel('Lane ID')
                    ax.set_ylabel('Number of Vehicles')
                    ax.set_title('Current Queue Lengths by Lane')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}', ha='center', va='bottom')
                    
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("✅ All lanes are clear - no queues detected!")
    else:
        st.info("Start the simulation to see real-time metrics")

with tab2:
    st.header("🚨 Emergency Vehicle Tracking")
    
    if running:
        metrics = load_metrics()
        emergency_vehicles = metrics.get('emergency_vehicle_list', [])
        
        if emergency_vehicles:
            st.subheader(f"Active Emergency Vehicles ({len(emergency_vehicles)})")
            
            df_emergency = pd.DataFrame(emergency_vehicles)
            
            if not df_emergency.empty:
                df_emergency['Status'] = df_emergency.apply(
                    lambda row: "🚨 Priority Active" if row.get('has_priority', False) else "⏳ In Traffic", 
                    axis=1
                )
                
                st.dataframe(
                    df_emergency[['vehicle_id', 'vehicle_type', 'current_lane', 'Status']],
                    column_config={
                        'vehicle_id': 'Vehicle ID',
                        'vehicle_type': 'Type',
                        'current_lane': 'Current Lane',
                        'Status': 'Status'
                    },
                    use_container_width=True
                )
                
                type_counts = df_emergency['vehicle_type'].value_counts()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Emergency Vehicle Types")
                    fig, ax = plt.subplots(figsize=(8, 6))
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
                    wedges, texts, autotexts = ax.pie(
                        type_counts.values, 
                        labels=type_counts.index, 
                        autopct='%1.1f%%',
                        colors=colors,
                        startangle=90
                    )
                    ax.set_title('Emergency Vehicle Distribution')
                    st.pyplot(fig)
                    plt.close()
                
                with col2:
                    st.subheader("Priority Interventions")
                    priority_count = df_emergency['has_priority'].sum() if 'has_priority' in df_emergency.columns else 0
                    total_emergency = len(df_emergency)
                    
                    st.metric("Active Priority Requests", priority_count)
                    st.metric("Total Emergency Vehicles", total_emergency)
                    
                    if total_emergency > 0:
                        priority_rate = (priority_count / total_emergency) * 100
                        st.metric("Priority Intervention Rate", f"{priority_rate:.1f}%")
        else:
            st.info("No emergency vehicles currently active in the simulation")
            
            st.subheader("Emergency Vehicle Configuration")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("🚑 **Ambulance**\n- Max Speed: 35 m/s\n- Priority: Highest\n- Color: Red")
            
            with col2:
                st.info("🚓 **Police**\n- Max Speed: 35 m/s\n- Priority: High\n- Color: Red")
            
            with col3:
                st.info("🚒 **Fire Truck**\n- Max Speed: 30 m/s\n- Priority: Highest\n- Color: Red")
    else:
        st.info("Start the simulation to see emergency vehicle tracking")

with tab3:
    st.header("🧠 AI Training Dashboard")
    
    if control_mode == "RL-based":
        if running:
            training_stats = load_training_stats()
            
            if training_stats.get('rewards') or training_stats.get('epsilon'):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Training Rewards")
                    if training_stats['rewards']:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(training_stats['rewards'], color='#45B7D1', linewidth=2)
                        ax.set_xlabel('Episode')
                        ax.set_ylabel('Total Reward')
                        ax.set_title('RL Agent Training Progress')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("No reward data available yet")
                
                with col2:
                    st.subheader("Exploration Rate (Epsilon)")
                    if training_stats['epsilon']:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(training_stats['epsilon'], color='#FF6B6B', linewidth=2)
                        ax.set_xlabel('Training Step')
                        ax.set_ylabel('Epsilon')
                        ax.set_title('Exploration vs Exploitation')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("No epsilon data available yet")
                
                if training_stats['losses']:
                    st.subheader("Training Loss")
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.plot(training_stats['losses'], color='#4ECDC4', linewidth=1, alpha=0.7)
                    
                    if len(training_stats['losses']) > 10:
                        window = 10
                        smoothed = pd.Series(training_stats['losses']).rolling(window=window).mean()
                        ax.plot(smoothed, color='#FF6B6B', linewidth=2, label=f'{window}-step moving average')
                        ax.legend()
                    
                    ax.set_xlabel('Training Step')
                    ax.set_ylabel('Loss')
                    ax.set_title('Training Loss Over Time')
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    plt.close()
            else:
                st.info("⏳ Training statistics will appear once the RL agent begins training...")
        else:
            st.info("Start the simulation in RL-based mode to see training statistics")
    else:
        st.info("Switch to RL-based mode to see AI training statistics")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if is_simulation_running():
    time.sleep(2)
    st.rerun()
