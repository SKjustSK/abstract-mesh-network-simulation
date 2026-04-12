import uuid
from utils import safe_print

class BroadcastNode:
    """Simulates an ESP32 LoRa Node operating as a transparent flood repeater."""
    def __init__(self, node_id, medium, x, y):
        self.node_id = node_id
        self.medium = medium
        
        # Ring buffer to track processed message IDs (prevents infinite broadcast storms)
        self.seen_messages = set()
        
        # Register physical coordinates with the RF physics engine
        self.medium.register_node(self, x, y)

    def initiate_broadcast(self, text):
        """Starts a completely new broadcast pulse from this node."""
        # Generate a unique 8-character ID for this specific transmission
        msg_id = str(uuid.uuid4())[:8]
        self.seen_messages.add(msg_id)
        
        packet = {
            'msg_id': msg_id, 
            'origin': self.node_id, 
            'payload': text, 
            'path': [self.node_id] # Track the exact nodes this packet bounces through
        }
        
        safe_print(f"\n[TX] {self.node_id} initiating BROADCAST: '{text}'")
        self.medium.transmit(self.node_id, packet)

    def receive(self, packet, relayed_by, rssi, dist):
        """Hardware Interrupt: Triggered when the RF medium delivers a packet."""
        # 1. Check if we've already repeated this specific message
        if packet['msg_id'] in self.seen_messages: 
            return
            
        # 2. Mark as seen to prevent repeating it again later
        self.seen_messages.add(packet['msg_id'])
        
        # 3. Append self to the routing path tracker
        updated_packet = packet.copy()
        updated_packet['path'] = packet['path'] + [self.node_id]
        
        safe_print(f"  [RX] {self.node_id} caught broadcast from {relayed_by} ({dist}m, {rssi}dBm)")
        
        # 4. Blindly rebroadcast to continue the mesh flood
        self.medium.transmit(self.node_id, updated_packet)