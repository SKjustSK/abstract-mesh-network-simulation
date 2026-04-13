import uuid
import time
from utils import log_only

class BroadcastNode:
    """Simulates an ESP32 LoRa Node operating as a transparent flood repeater."""
    def __init__(self, node_id, medium, x, y):
        self.node_id = node_id
        self.medium = medium
        
        self.seen_messages = set()
        
        # --- NEW METRIC TRACKERS ---
        self.duplicates_dropped = 0
        self.successful_rx_data = [] 
        
        self.medium.register_node(self, x, y)

    def initiate_broadcast(self, text):
        """Starts a completely new broadcast pulse from this node."""
        msg_id = str(uuid.uuid4())[:8]
        self.seen_messages.add(msg_id)
        
        packet = {
            'msg_id': msg_id, 
            'origin': self.node_id, 
            'payload': text, 
            'path': [self.node_id],
            'start_time': time.time() # Timestamp to calculate latency later
        }
        
        log_only(f"\n[TX] {self.node_id} initiating BROADCAST: '{text}'")
        self.medium.transmit(self.node_id, packet)

    def receive(self, packet, relayed_by, rssi, dist):
        """Hardware Interrupt: Triggered when the RF medium delivers a packet."""
        # 1. Track dropped duplicates for Network Overhead metrics
        if packet['msg_id'] in self.seen_messages: 
            self.duplicates_dropped += 1
            return
            
        # 2. Mark as seen to prevent repeating it again later
        self.seen_messages.add(packet['msg_id'])
        
        updated_packet = packet.copy()
        updated_packet['path'] = packet['path'] + [self.node_id]
        
        log_only(f"  [RX] {self.node_id} caught broadcast from {relayed_by} ({dist}m, {rssi}dBm)")
        
        # 3. If this node is the intended target, log the success metrics
        target_id = f"Node_{packet['payload'].split(']')[0].split('_')[1]}"
        if self.node_id == target_id:
            self.successful_rx_data.append({
                'hops': len(updated_packet['path']) - 1,
                'rssi': rssi,
                'start_time': packet['start_time'],
                'end_time': time.time()
            })
        
        # 4. Blindly rebroadcast to continue the mesh flood
        self.medium.transmit(self.node_id, updated_packet)