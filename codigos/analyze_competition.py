#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
import argparse
from helper import read_list

def parse_ping_results(ping_file):
    """Parse ping results to extract RTT statistics."""
    if not os.path.exists(ping_file):
        return None
    
    rtts = []
    with open(ping_file, 'r') as f:
        for line in f:
            if 'time=' in line:
                # Extract RTT value
                parts = line.split('time=')
                if len(parts) > 1:
                    rtt_str = parts[1].split()[0]
                    try:
                        rtt = float(rtt_str)
                        rtts.append(rtt)
                    except ValueError:
                        continue
    
    if rtts:
        return {
            'rtts': rtts,
            'avg_rtt': np.mean(rtts),
            'min_rtt': np.min(rtts),
            'max_rtt': np.max(rtts),
            'std_rtt': np.std(rtts)
        }
    return None

def parse_queue_results(queue_file):
    """Parse queue length results."""
    if not os.path.exists(queue_file):
        return None
    
    queue_data = read_list(queue_file)
    if not queue_data:
        return None
    
    times = []
    queue_lengths = []
    
    for row in queue_data:
        if len(row) >= 2:
            try:
                times.append(float(row[0]))
                queue_lengths.append(int(row[1]))
            except ValueError:
                continue
    
    if queue_lengths:
        return {
            'times': times,
            'queue_lengths': queue_lengths,
            'avg_queue': np.mean(queue_lengths),
            'max_queue': np.max(queue_lengths),
            'queue_utilization': np.mean(queue_lengths) / 100.0  # Assuming max queue is 100
        }
    return None

def plot_competition_results(results_dir):
    """Create comprehensive plots of competition results."""
    
    # Load competition results
    results_file = os.path.join(results_dir, 'competition_results.json')
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            results = json.load(f)
    else:
        results = {}
    
    # Parse additional data
    ping_reno = parse_ping_results(os.path.join(results_dir, 'ping_reno.txt'))
    ping_bbr = parse_ping_results(os.path.join(results_dir, 'ping_bbr.txt'))
    queue_data = parse_queue_results(os.path.join(results_dir, 'queue.txt'))
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('TCP Competition: Reno vs BBR', fontsize=16)
    
    # Plot 1: Throughput comparison
    ax1 = axes[0, 0]
    if 'reno_flow' in results and 'bbr_flow' in results:
        algorithms = ['TCP Reno', 'TCP BBR']
        throughputs = [results['reno_flow']['avg_throughput'], 
                      results['bbr_flow']['avg_throughput']]
        colors = ['blue', 'red']
        
        bars = ax1.bar(algorithms, throughputs, color=colors, alpha=0.7)
        ax1.set_ylabel('Average Throughput (Mbps)')
        ax1.set_title('Throughput Comparison')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars, throughputs):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}', ha='center', va='bottom')
    
    # Plot 2: RTT comparison
    ax2 = axes[0, 1]
    if ping_reno and ping_bbr:
        rtt_data = [ping_reno['rtts'], ping_bbr['rtts']]
        labels = ['TCP Reno', 'TCP BBR']
        colors = ['blue', 'red']
        
        box_plot = ax2.boxplot(rtt_data, labels=labels, patch_artist=True)
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax2.set_ylabel('RTT (ms)')
        ax2.set_title('RTT Distribution')
        ax2.grid(True, alpha=0.3)
    
    # Plot 3: Queue length over time
    ax3 = axes[1, 0]
    if queue_data:
        # Convert timestamps to relative time
        start_time = min(queue_data['times'])
        relative_times = [(t - start_time) for t in queue_data['times']]
        
        ax3.plot(relative_times, queue_data['queue_lengths'], 'g-', linewidth=1)
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Queue Length (packets)')
        ax3.set_title('Queue Length Over Time')
        ax3.grid(True, alpha=0.3)
    
    # Plot 4: Fairness and efficiency metrics
    ax4 = axes[1, 1]
    if 'fairness_index' in results:
        metrics = ['Fairness Index', 'Total Throughput', 'Queue Utilization']
        values = [
            results['fairness_index'],
            (results['reno_flow']['avg_throughput'] + results['bbr_flow']['avg_throughput']) / 2,
            queue_data['queue_utilization'] if queue_data else 0
        ]
        
        # Normalize values for better visualization
        normalized_values = [
            values[0],  # Fairness index is already 0-1
            values[1] / 100,  # Normalize throughput
            values[2]   # Queue utilization is already 0-1
        ]
        
        bars = ax4.bar(metrics, normalized_values, color=['purple', 'orange', 'green'], alpha=0.7)
        ax4.set_ylabel('Normalized Value')
        ax4.set_title('Performance Metrics')
        ax4.set_ylim(0, 1.1)
        ax4.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, val, orig_val in zip(bars, normalized_values, values):
            if 'Fairness' in bar.get_x():
                label = f'{orig_val:.3f}'
            elif 'Throughput' in bar.get_x():
                label = f'{orig_val:.1f} Mbps'
            else:
                label = f'{orig_val:.1%}'
            
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    label, ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'competition_analysis.png'), dpi=300, bbox_inches='tight')
    plt.show()

def print_detailed_analysis(results_dir):
    """Print detailed analysis of competition results."""
    
    results_file = os.path.join(results_dir, 'competition_results.json')
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print("="*60)
    print("DETAILED TCP COMPETITION ANALYSIS")
    print("="*60)
    
    if 'reno_flow' in results and 'bbr_flow' in results:
        reno = results['reno_flow']
        bbr = results['bbr_flow']
        
        print(f"\nTCP RENO METRICS:")
        print(f"  Average Throughput: {reno['avg_throughput']:.2f} Mbps")
        print(f"  Min Throughput: {reno['min_throughput']:.2f} Mbps")
        print(f"  Max Throughput: {reno['max_throughput']:.2f} Mbps")
        print(f"  Std Deviation: {reno['std_throughput']:.2f} Mbps")
        
        print(f"\nTCP BBR METRICS:")
        print(f"  Average Throughput: {bbr['avg_throughput']:.2f} Mbps")
        print(f"  Min Throughput: {bbr['min_throughput']:.2f} Mbps")
        print(f"  Max Throughput: {bbr['max_throughput']:.2f} Mbps")
        print(f"  Std Deviation: {bbr['std_throughput']:.2f} Mbps")
        
        print(f"\nCOMPETITION ANALYSIS:")
        print(f"  Winner: {results.get('winner', 'N/A')}")
        print(f"  Advantage: {results.get('advantage', 0):.1f}%")
        print(f"  Fairness Index: {results.get('fairness_index', 'N/A'):.3f}")
        
        # Interpret fairness index
        fairness = results.get('fairness_index', 0)
        if fairness >= 0.9:
            fairness_desc = "Excellent fairness"
        elif fairness >= 0.7:
            fairness_desc = "Good fairness"
        elif fairness >= 0.5:
            fairness_desc = "Moderate fairness"
        else:
            fairness_desc = "Poor fairness"
        
        print(f"  Fairness Assessment: {fairness_desc}")
        
        # Calculate efficiency
        total_throughput = reno['avg_throughput'] + bbr['avg_throughput']
        print(f"  Total Throughput: {total_throughput:.2f} Mbps")
        print(f"  Efficiency: {total_throughput:.1f}% of available bandwidth")
    
    # RTT Analysis
    ping_reno = parse_ping_results(os.path.join(results_dir, 'ping_reno.txt'))
    ping_bbr = parse_ping_results(os.path.join(results_dir, 'ping_bbr.txt'))
    
    if ping_reno and ping_bbr:
        print(f"\nRTT ANALYSIS:")
        print(f"  TCP Reno RTT: {ping_reno['avg_rtt']:.2f} ± {ping_reno['std_rtt']:.2f} ms")
        print(f"  TCP BBR RTT: {ping_bbr['avg_rtt']:.2f} ± {ping_bbr['std_rtt']:.2f} ms")
        
        # Compare RTT stability
        reno_cv = ping_reno['std_rtt'] / ping_reno['avg_rtt']
        bbr_cv = ping_bbr['std_rtt'] / ping_bbr['avg_rtt']
        
        if reno_cv < bbr_cv:
            print(f"  RTT Stability: TCP Reno is more stable (CV: {reno_cv:.3f} vs {bbr_cv:.3f})")
        else:
            print(f"  RTT Stability: TCP BBR is more stable (CV: {bbr_cv:.3f} vs {reno_cv:.3f})")
    
    # Queue Analysis
    queue_data = parse_queue_results(os.path.join(results_dir, 'queue.txt'))
    if queue_data:
        print(f"\nQUEUE ANALYSIS:")
        print(f"  Average Queue Length: {queue_data['avg_queue']:.1f} packets")
        print(f"  Maximum Queue Length: {queue_data['max_queue']} packets")
        print(f"  Queue Utilization: {queue_data['queue_utilization']:.1%}")
        
        if queue_data['queue_utilization'] > 0.8:
            print("  Assessment: High queue utilization - potential bufferbloat")
        elif queue_data['queue_utilization'] > 0.5:
            print("  Assessment: Moderate queue utilization")
        else:
            print("  Assessment: Low queue utilization - underutilized buffer")

def main():
    parser = argparse.ArgumentParser(description="Analyze TCP competition results")
    parser.add_argument('--dir', '-d', required=True, help="Results directory")
    parser.add_argument('--plot', action='store_true', help="Generate plots")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"Results directory not found: {args.dir}")
        sys.exit(1)
    
    print_detailed_analysis(args.dir)
    
    if args.plot:
        plot_competition_results(args.dir)

if __name__ == "__main__":
    main()
