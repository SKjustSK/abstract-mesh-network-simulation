import time
from utils import safe_print
from rf_medium import JungleMedium
from node import BroadcastNode

def main():
    # 1. Initialize the RF Physics Engine
    medium = JungleMedium()
    max_range = medium.get_max_range()
    
    # 2. Calculate absolute X-coordinates based on relative percentage steps
    # A to B: 25%, B to C: 25%, C to D: 25%, D to E: 200%
    pos_A = 0
    pos_B = pos_A + (max_range * 0.25)
    pos_C = pos_B + (max_range * 0.25)
    pos_D = pos_C + (max_range * 0.25)
    pos_E = pos_D + (max_range * 2.0)
    
    # 3. Instantiate the nodes on the grid
    nodes = {
        "A": BroadcastNode("Node_A", medium, pos_A, 0),
        "B": BroadcastNode("Node_B", medium, pos_B, 0),
        "C": BroadcastNode("Node_C", medium, pos_C, 0),
        "D": BroadcastNode("Node_D", medium, pos_D, 0),
        "E": BroadcastNode("Node_E", medium, pos_E, 0)
    }

    # 4. Render the Terminal Dashboard
    print("\n--- JUNGLE BROADCAST MESH DASHBOARD ---")
    print("Formation: A -> B -> C -> D -> E")
    print(f"Theo. Max Range: {max_range:.1f} meters")
    print("-" * 40)
    print(f"Dist A->B: {max_range * 0.25:.1f} m (25% of Max)")
    print(f"Dist B->C: {max_range * 0.25:.1f} m (25% of Max)")
    print(f"Dist C->D: {max_range * 0.25:.1f} m (25% of Max)")
    print(f"Dist D->E: {max_range * 2.0:.1f} m (200% of Max - BORDERLINE)")
    print("-" * 40)

    # 5. Main Application Loop
    while True:
        print("\n1. Send Custom Broadcast Pulse")
        print("2. Exit")
        choice = input("Action: ")
        
        if choice == '1':
            # Get transmission parameters from the user
            src_key = input("Enter Source Node (A, B, C, D, E): ").upper()
            if src_key not in nodes:
                print("Invalid Source Node.")
                continue
                
            dest_key = input("Enter Destination Node (A, B, C, D, E): ").upper()
            if dest_key not in nodes:
                print("Invalid Destination Node.")
                continue
                
            custom_msg = input("Enter your message: ")
            
            # Clear the memory buffers so nodes will accept the new pulse
            for n in nodes.values(): 
                n.seen_messages.clear()
            
            # Format the payload so all nodes know who the intended recipient is
            payload = f"[Target: Node_{dest_key}] {custom_msg}"
            
            # Fire the starting packet from the selected Source Node
            nodes[src_key].initiate_broadcast(payload)
            
            # Wait for the slow SF12 LoRa transmissions to cascade down the chain
            time.sleep(8.0) 
            
            # Compile the final reach report
            reached = [n.node_id for n in nodes.values() if len(n.seen_messages) > 0]
            
            safe_print("\n" + "="*56)
            
            # Check if the intended destination actually received the payload
            if f"Node_{dest_key}" in reached or src_key == dest_key:
                safe_print(f"SUCCESS: '{custom_msg}' successfully reached Node_{dest_key}!")
            else:
                safe_print(f"FAILED: The jungle blocked the signal before it reached Node_{dest_key}.")
                
            safe_print(f"NETWORK REPORT: Signal was heard by -> {', '.join(reached)}")
            safe_print("="*56)
            
        elif choice == '2':
            print("Shutting down simulator...")
            break
        else:
            print("Invalid choice. Please select 1 or 2.")

if __name__ == "__main__":
    main()