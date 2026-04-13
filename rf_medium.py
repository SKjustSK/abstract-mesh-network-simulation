import math
import time
import threading
import random
from utils import log_only

class JungleMedium:
    """Simulates RF using the Experimental Forest Path Loss Model."""
    def __init__(self, **kwargs):
        self.nodes = {}
        
        self.f = kwargs.get('f', 433000000)                 
        self.tx_power_dbm = kwargs.get('tx_power_dbm', 20)  
        self.rx_sensitivity = kwargs.get('rx_sensitivity', -136) 
        self.alpha = kwargs.get('alpha', 0.5)               
        self.beta = kwargs.get('beta', 0.2)                 
        self.gamma_const = kwargs.get('gamma_const', 0.3)   
        self.rho = kwargs.get('rho', 0.12)                  
        self.h = kwargs.get('h', 18)                        
        self.sigma = kwargs.get('sigma', 6.5)               
        
        self.time_scale = kwargs.get('time_scale', 1.0)

    def calculate_path_loss(self, d):
        if d <= 0: return 0
        A = self.alpha * self.rho * (1 - math.exp(-self.beta * self.rho))
        B = self.gamma_const * self.h
        pl_base = (20 * math.log10(d)) + (10 * math.log10(self.f))
        return pl_base + A - B + random.gauss(0, self.sigma)

    def get_max_range(self):
        A = self.alpha * self.rho * (1 - math.exp(-self.beta * self.rho))
        B = self.gamma_const * self.h
        target_pl = self.tx_power_dbm - self.rx_sensitivity
        log_d = (target_pl - 10*math.log10(self.f) - A + B) / 20
        return 10 ** log_d

    def register_node(self, node, x, y):
        self.nodes[node.node_id] = {'node': node, 'x': x, 'y': y}

    def transmit(self, sender_id, packet):
        # Apply the time scale to the simulated 1.5s airtime delay
        time.sleep(1.5 * self.time_scale) 
        sender_coords = self.nodes[sender_id]
        
        for neighbor_id, neighbor_data in self.nodes.items():
            if neighbor_id == sender_id: continue
                
            dist = math.sqrt((neighbor_data['x'] - sender_coords['x'])**2 + 
                             (neighbor_data['y'] - sender_coords['y'])**2)
            
            rssi = self.tx_power_dbm - self.calculate_path_loss(dist)

            if rssi >= self.rx_sensitivity:
                threading.Thread(
                    target=neighbor_data['node'].receive, 
                    args=(packet, sender_id, round(rssi, 1), round(dist, 1))
                ).start()
            else:
                log_only(f"      [LOST] {sender_id} -> {neighbor_id} ({round(dist, 0)}m | {round(rssi, 1)}dBm)")