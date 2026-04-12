import math
import time
import threading
import random
from utils import safe_print

class JungleMedium:
    """Simulates RF using the Experimental Forest Path Loss Model (Eq. 5)."""
    def __init__(self):
        self.nodes = {}
        
        # --- HARDWARE CONSTANTS (Ai-Thinker Ra-02 / SX1278) ---
        # f: Operating Frequency. 433 MHz is standard for high-penetration LoRa.
        self.f = 433000000          
        # tx_power_dbm: 20 dBm (100mW) is the absolute maximum output for the module.
        self.tx_power_dbm = 20       
        # rx_sensitivity: -136 dBm is the threshold for Spreading Factor 12 (SF12) at 125 kHz bandwidth.
        self.rx_sensitivity = -136   
        
        # --- JUNGLE / FOREST EMPIRICAL CONSTANTS ---
        # alpha: Path loss per unit tree density (dB/m^2).
        self.alpha = 0.5             
        # beta: The exponential slope/decay rate of the path loss curve.
        self.beta = 0.2              
        # gamma_const: Path loss per unit tree height (dB/m).
        self.gamma_const = 0.3       
        
        # --- ENVIRONMENTAL VARIABLES ---
        # rho: Tree Density (trees per square meter). 0.12 = highly dense tropical jungle.
        self.rho = 0.12              
        # h: Average Tree Height (meters). Taller trees slightly reduce loss by providing 'trunk space'.
        self.h = 18                  
        # sigma: Standard deviation for Log-Normal Shadowing. Simulates random RF blocks (rocks, wet canopy).
        self.sigma = 6.5             

    def calculate_path_loss(self, d):
        """
        Calculates total signal degradation over distance 'd' using the Generalized Forest Model:
        PL = 20*log10(d) + 10*log10(f) + A - B + Shadowing
        """
        if d <= 0: return 0
        
        # Formula: Attenuation due to tree density (A)
        # A = α * ρ * (1 - e^(-β * ρ))
        A = self.alpha * self.rho * (1 - math.exp(-self.beta * self.rho))
        
        # Formula: Attenuation reduction due to tree height (B)
        # B = γ * h
        B = self.gamma_const * self.h
        
        # Formula: Base Path Loss (Simplified Free Space component)
        pl_base = (20 * math.log10(d)) + (10 * math.log10(self.f))
        
        # Final calculation with Gaussian random noise (Shadowing) added to simulate reality
        return pl_base + A - B + random.gauss(0, self.sigma)

    def get_max_range(self):
        """
        Derives the theoretical maximum range by reversing the Path Loss equation.
        Finds 'd' where Expected Path Loss perfectly equals the Link Budget.
        Link Budget = Tx Power - Rx Sensitivity.
        """
        A = self.alpha * self.rho * (1 - math.exp(-self.beta * self.rho))
        B = self.gamma_const * self.h
        
        target_pl = self.tx_power_dbm - self.rx_sensitivity
        
        # Reversing the base equation: 20*log10(d) = Target_PL - 10*log10(f) - A + B
        log_d = (target_pl - 10*math.log10(self.f) - A + B) / 20
        return 10 ** log_d

    def register_node(self, node, x, y):
        """Adds a node to the spatial simulation grid."""
        self.nodes[node.node_id] = {'node': node, 'x': x, 'y': y}

    def transmit(self, sender_id, packet):
        """Simulates an omnidirectional LoRa broadcast to all registered nodes."""
        # Simulate physical airtime delay (SF12 takes ~1.5s to transmit)
        time.sleep(1.5) 
        sender_coords = self.nodes[sender_id]
        
        for neighbor_id, neighbor_data in self.nodes.items():
            if neighbor_id == sender_id: continue
                
            # Calculate Euclidean distance between sender and neighbor
            dist = math.sqrt((neighbor_data['x'] - sender_coords['x'])**2 + 
                             (neighbor_data['y'] - sender_coords['y'])**2)
            
            # Formula: Final Received Signal Strength (RSSI) = Tx Power - Path Loss
            rssi = self.tx_power_dbm - self.calculate_path_loss(dist)

            # Check if the signal is loud enough for the SX1278 chip to hear
            if rssi >= self.rx_sensitivity:
                # Trigger an asynchronous interrupt on the receiving node
                threading.Thread(
                    target=neighbor_data['node'].receive, 
                    args=(packet, sender_id, round(rssi, 1), round(dist, 1))
                ).start()
            else:
                safe_print(f"      [LOST] {sender_id} -> {neighbor_id} ({round(dist, 0)}m | {round(rssi, 1)}dBm)")