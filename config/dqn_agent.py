import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from config.traffic_controller import TrafficController
import os

class DQNNetwork(nn.Module):
    def __init__(self, state_size, action_size, hidden_size=128):
        super(DQNNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, 64)
        self.fc4 = nn.Linear(64, action_size)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout(x)
        x = torch.relu(self.fc3(x))
        x = self.fc4(x)
        return x

class DQNAgent(TrafficController):
    def __init__(self, tls_ids, state_size=30, action_size=4, lr=0.001):
        super().__init__(tls_ids)
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = lr
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.q_network = DQNNetwork(state_size, action_size).to(self.device)
        self.target_network = DQNNetwork(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=lr)
        
        self.update_target_network()
        
        self.training_stats = {
            'rewards': [],
            'epsilon': [],
            'losses': []
        }
        
        self.episode_reward = 0
        self.episode_step = 0
        self.last_state = {}
        self.last_action = {}
        self.last_throughput = 0
        
    def update_target_network(self):
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def get_state(self, tls_id):
        """Get state representation"""
        import traci
        try:
            queue_lengths, waiting_times, occupancy = self.get_lane_data(tls_id)
            emergency_vehicles = self.get_emergency_vehicles(tls_id)
            
            state = []
            
            queue_values = list(queue_lengths.values())[:10]
            queue_values.extend([0] * (10 - len(queue_values)))
            state.extend([min(q/20, 1.0) for q in queue_values])
            
            wait_values = list(waiting_times.values())[:10]
            wait_values.extend([0] * (10 - len(wait_values)))
            state.extend([min(w/120, 1.0) for w in wait_values])
            
            current_phase = traci.trafficlight.getPhase(tls_id)
            phase_duration = self.get_phase_duration(tls_id)
            state.extend([current_phase/4, min(phase_duration/60, 1.0)])
            
            emergency_count = len(emergency_vehicles)
            state.extend([min(emergency_count/5, 1.0)])
            
            controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
            total_vehicles = sum(traci.lane.getLastStepVehicleNumber(lane) 
                               for lane in set(controlled_lanes))
            state.extend([min(total_vehicles/50, 1.0)])
            
            occupancy_values = list(occupancy.values())[:6]
            occupancy_values.extend([0] * (6 - len(occupancy_values)))
            state.extend(occupancy_values)
            
            while len(state) < self.state_size:
                state.append(0.0)
            
            return np.array(state[:self.state_size], dtype=np.float32)
            
        except Exception as e:
            print(f"Error getting state: {e}")
            return np.zeros(self.state_size, dtype=np.float32)
    
    def decide_phase(self, tls_id):
        """Decide phase using DQN"""
        try:
            emergency_vehicles = self.get_emergency_vehicles(tls_id)
            if emergency_vehicles:
                return self._handle_emergency(tls_id, emergency_vehicles)
            
            state = self.get_state(tls_id)
            
            if random.random() <= self.epsilon:
                action = random.randrange(self.action_size)
            else:
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.q_network(state_tensor)
                action = q_values.argmax().item()
            
            if tls_id in self.last_state:
                self.remember(tls_id, action, state)
            
            self.last_state[tls_id] = state
            self.last_action[tls_id] = action
            self.episode_step += 1
            
            return action
            
        except Exception as e:
            print(f"Error in decide_phase: {e}")
            return 0
    
    def _handle_emergency(self, tls_id, emergency_vehicles):
        """Handle emergency vehicles"""
        emergency_lane = emergency_vehicles[0][1]
        return self._get_phase_for_lane(tls_id, emergency_lane)
    
    def _get_phase_for_lane(self, tls_id, lane):
        """Get phase for lane"""
        import traci
        try:
            controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
            logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
            
            for phase_idx, phase in enumerate(logic.phases):
                state = phase.state
                for i, lane_id in enumerate(controlled_lanes):
                    if lane_id == lane and i < len(state):
                        if state[i] in ['G', 'g']:
                            return phase_idx
            return 0
        except:
            return 0
    
    def remember(self, tls_id, action, new_state):
        """Store experience"""
        if tls_id in self.last_state:
            reward = self.calculate_reward(tls_id)
            self.memory.append((
                self.last_state[tls_id],
                self.last_action[tls_id],
                reward,
                new_state,
                False
            ))
            self.episode_reward += reward
    
    def calculate_reward(self, tls_id):
        """Calculate reward"""
        try:
            queue_lengths, waiting_times, _ = self.get_lane_data(tls_id)
            
            queue_penalty = -sum(queue_lengths.values()) * 0.1
            wait_penalty = -sum(waiting_times.values()) * 0.01
            
            emergency_vehicles = self.get_emergency_vehicles(tls_id)
            emergency_bonus = len(emergency_vehicles) * 2.0
            
            total_reward = queue_penalty + wait_penalty + emergency_bonus
            return max(-10, min(10, total_reward))
            
        except:
            return -1.0
    
    def replay(self, batch_size=32):
        """Train the network"""
        if len(self.memory) < batch_size:
            return None
            
        try:
            batch = random.sample(self.memory, batch_size)
            states = torch.FloatTensor([e[0] for e in batch]).to(self.device)
            actions = torch.LongTensor([e[1] for e in batch]).to(self.device)
            rewards = torch.FloatTensor([e[2] for e in batch]).to(self.device)
            next_states = torch.FloatTensor([e[3] for e in batch]).to(self.device)
            dones = torch.BoolTensor([e[4] for e in batch]).to(self.device)
            
            current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
            next_q_values = self.target_network(next_states).max(1)[0].detach()
            target_q_values = rewards + (0.99 * next_q_values * ~dones)
            
            loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
            
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
            self.optimizer.step()
            
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            
            self.training_stats['losses'].append(loss.item())
            self.training_stats['epsilon'].append(self.epsilon)
            
            return loss.item()
            
        except Exception as e:
            print(f"Error in replay: {e}")
            return None
    
    def update_throughput(self):
        """Update throughput tracking"""
        try:
            if self.episode_step > 0 and self.episode_step % 100 == 0:
                self.training_stats['rewards'].append(self.episode_reward)
                self.episode_reward = 0
                
                if len(self.training_stats['rewards']) % 10 == 0:
                    self.update_target_network()
        except:
            pass
    
    def save_model(self, filepath):
        """Save model"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            torch.save({
                'q_network_state_dict': self.q_network.state_dict(),
                'target_network_state_dict': self.target_network.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'training_stats': self.training_stats
            }, filepath)
            print(f"Model saved to {filepath}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self, filepath):
        """Load model"""
        try:
            checkpoint = torch.load(filepath, map_location=self.device)
            self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
            self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.epsilon = checkpoint.get('epsilon', self.epsilon_min)
            self.training_stats = checkpoint.get('training_stats', self.training_stats)
            print(f"Model loaded from {filepath}")
        except Exception as e:
            print(f"Error loading model: {e}")
