import time
from utils import safe_print, log_only
from rf_medium import JungleMedium
from node import BroadcastNode

# ==========================================
# --- CENTRAL SIMULATION CONFIGURATION ---
# ==========================================
SIM_CONFIG = {
    'time_scale': 0.05,             # 1.0 = Real-time LoRa speeds, 0.05 = Fast simulation
    'stress_test_packets': 50,      # Number of packets to send during the test
    'f': 433000000,                 
    'tx_power_dbm': 20,             
    'rx_sensitivity': -136,         
    'rho': 0.12,                    # tree density
    'h': 18,                        # average tree height
    'sigma': 6.5,                   # deviation for shadowing
    'dist_mult_AB': 0.25,           
    'dist_mult_BC': 0.25,           
    'dist_mult_CD': 0.25,           
    'dist_mult_DE': 2.0             
}
# ==========================================

def main():
    medium = JungleMedium(**SIM_CONFIG)
    max_range = medium.get_max_range()
    
    pos_A = 0
    pos_B = pos_A + (max_range * SIM_CONFIG['dist_mult_AB'])
    pos_C = pos_B + (max_range * SIM_CONFIG['dist_mult_BC'])
    pos_D = pos_C + (max_range * SIM_CONFIG['dist_mult_CD'])
    pos_E = pos_D + (max_range * SIM_CONFIG['dist_mult_DE'])
    
    nodes = {
        "A": BroadcastNode("Node_A", medium, pos_A, 0),
        "B": BroadcastNode("Node_B", medium, pos_B, 0),
        "C": BroadcastNode("Node_C", medium, pos_C, 0),
        "D": BroadcastNode("Node_D", medium, pos_D, 0),
        "E": BroadcastNode("Node_E", medium, pos_E, 0)
    }

    session_packets_sent = 0
    session_packets_delivered = 0

    safe_print("\n--- JUNGLE BROADCAST MESH DASHBOARD ---")
    safe_print("Formation: A -> B -> C -> D -> E")
    safe_print(f"Theo. Max Range: {max_range:.1f} meters")
    safe_print(f"Simulation Speed: {SIM_CONFIG['time_scale']}x real-time")
    safe_print("-" * 40)
    safe_print(f"Dist A->B: {max_range * SIM_CONFIG['dist_mult_AB']:.1f} m ({SIM_CONFIG['dist_mult_AB']*100:.0f}% of Max)")
    safe_print(f"Dist B->C: {max_range * SIM_CONFIG['dist_mult_BC']:.1f} m ({SIM_CONFIG['dist_mult_BC']*100:.0f}% of Max)")
    safe_print(f"Dist C->D: {max_range * SIM_CONFIG['dist_mult_CD']:.1f} m ({SIM_CONFIG['dist_mult_CD']*100:.0f}% of Max)")
    safe_print(f"Dist D->E: {max_range * SIM_CONFIG['dist_mult_DE']:.1f} m ({SIM_CONFIG['dist_mult_DE']*100:.0f}% of Max)")
    safe_print("-" * 40)

    while True:
        print(f"\n1. Run Automated PDR Stress Test ({SIM_CONFIG['stress_test_packets']} Packets)")
        print("2. Exit")
        choice = input("Action: ")
        
        if choice == '1':
            src_key = input("Enter Source Node for Test (e.g., A): ").upper()
            dest_key = input("Enter Destination Node for Test (e.g., E): ").upper()
            
            if src_key not in nodes or dest_key not in nodes:
                print("Invalid nodes selected.")
                continue
                
            test_count = SIM_CONFIG['stress_test_packets']
            test_delivered = 0
            
            # Reset the advanced metric trackers before starting the batch
            for n in nodes.values():
                n.duplicates_dropped = 0
                n.successful_rx_data.clear()
            
            safe_print(f"\n--- RUNNING PDR STRESS TEST: {test_count} Packets ({src_key} -> {dest_key}) ---")
            print("Simulating network traffic... Check 'simulation_log.txt' for exact packet routing details.")
            
            for i in range(test_count):
                for n in nodes.values(): 
                    n.seen_messages.clear()
                
                payload = f"[Target: Node_{dest_key}] Stress Test Packet {i+1}/{test_count}"
                session_packets_sent += 1
                
                nodes[src_key].initiate_broadcast(payload)
                time.sleep(8.0 * SIM_CONFIG['time_scale']) 
                
                reached = [n.node_id for n in nodes.values() if len(n.seen_messages) > 0]
                if f"Node_{dest_key}" in reached or src_key == dest_key:
                    test_delivered += 1
                    session_packets_delivered += 1
            
            # --- CALCULATE METRICS ---
            test_pdr = (test_delivered / test_count) * 100
            global_pdr = (session_packets_delivered / session_packets_sent) * 100
            
            total_duplicates = sum(n.duplicates_dropped for n in nodes.values())
            dest_node_obj = nodes[dest_key]
            
            avg_hops, avg_rssi, avg_latency = 0, 0, 0
            
            if len(dest_node_obj.successful_rx_data) > 0:
                total_hops = sum(d['hops'] for d in dest_node_obj.successful_rx_data)
                total_rssi = sum(d['rssi'] for d in dest_node_obj.successful_rx_data)
                
                # Reverse the time scale to calculate what the real-world latency would have been
                total_latency = sum((d['end_time'] - d['start_time']) / SIM_CONFIG['time_scale'] for d in dest_node_obj.successful_rx_data)
                
                avg_hops = total_hops / len(dest_node_obj.successful_rx_data)
                avg_rssi = total_rssi / len(dest_node_obj.successful_rx_data)
                avg_latency = total_latency / len(dest_node_obj.successful_rx_data)
            
            # --- OUTPUT FINAL REPORT ---
            safe_print("\n" + "="*65)
            safe_print(f"STRESS TEST COMPLETE ({src_key} -> {dest_key})")
            safe_print(f"Batch PDR:           {test_pdr:.1f}% ({test_delivered}/{test_count} delivered successfully)")
            safe_print(f"Global Session PDR:  {global_pdr:.1f}% ({session_packets_delivered}/{session_packets_sent} total)")
            safe_print("-" * 65)
            safe_print(f"Avg Hops Taken:      {avg_hops:.1f} hops")
            safe_print(f"Avg End-to-End Time: {avg_latency:.2f} seconds (simulated real-world)")
            safe_print(f"Avg Arrival RSSI:    {avg_rssi:.1f} dBm (Failure Threshold: {SIM_CONFIG['rx_sensitivity']} dBm)")
            safe_print(f"Network Overhead:    {total_duplicates} redundant packets dropped by nodes")
            safe_print("="*65)

        elif choice == '2':
            safe_print("Shutting down simulator...")
            break
        else:
            print("Invalid choice. Please select 1 or 2.")

if __name__ == "__main__":
    main()