#!/usr/bin/env python3

"""
Visualização da Competição TCP: Reno vs BBR
Script para criar gráficos interativos da disputa entre algoritmos TCP
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import json
import os
import sys
import argparse
from datetime import datetime
import pandas as pd
from matplotlib.patches import Rectangle
import seaborn as sns

# Configurar estilo dos gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def parse_iperf_timeline(file_path):
    """Parse iperf output to extract throughput timeline."""
    throughputs = []
    timestamps = []
    
    if not os.path.exists(file_path):
        return [], []
    
    with open(file_path, 'r') as f:
        for line in f:
            if 'Mbits/sec' in line and 'sec' in line:
                parts = line.strip().split()
                
                # Extract time interval
                time_part = parts[2]  # Should be like "0.0-1.0"
                if '-' in time_part:
                    end_time = float(time_part.split('-')[1])
                    timestamps.append(end_time)
                
                # Extract throughput
                for i, part in enumerate(parts):
                    if part == 'Mbits/sec' and i > 0:
                        try:
                            throughput = float(parts[i-1])
                            throughputs.append(throughput)
                        except ValueError:
                            continue
                        break
    
    return timestamps, throughputs

def create_competition_timeline_plot(results_dir):
    """Create animated timeline plot showing the competition."""
    
    # Parse data - support multiple flows
    flow_data = {}
    
    # Look for all flow output files
    for file in os.listdir(results_dir):
        if file.endswith('_output.txt'):
            flow_name = file.replace('_output.txt', '')
            times, throughputs = parse_iperf_timeline(os.path.join(results_dir, file))
            if times and throughputs:
                flow_data[flow_name] = {'times': times, 'throughputs': throughputs}
    
    if not flow_data:
        print("Erro: Dados de throughput não encontrados")
        return
    
    # Create figure
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('TCP Competition Timeline', fontsize=16, fontweight='bold')
    
    # Colors for different flows
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    reno_color = 'blue'
    bbr_color = 'red'
    
    # Plot 1: Throughput over time
    flow_index = 0
    reno_flows = []
    bbr_flows = []
    
    for flow_name, data in flow_data.items():
        if 'reno' in flow_name.lower():
            color = reno_color
            reno_flows.append(data)
        elif 'bbr' in flow_name.lower():
            color = bbr_color
            bbr_flows.append(data)
        else:
            color = colors[flow_index % len(colors)]
        
        ax1.plot(data['times'], data['throughputs'], color=color, linewidth=2, 
                label=flow_name, marker='o', markersize=3)
        flow_index += 1
    
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Throughput Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cumulative throughput by algorithm
    if reno_flows and bbr_flows:
        # Calculate total throughput for each algorithm
        max_time = max(max(data['times']) for data in flow_data.values())
        time_points = np.arange(0, max_time + 1)
        
        reno_total = np.zeros(len(time_points))
        bbr_total = np.zeros(len(time_points))
        
        for t_idx, t in enumerate(time_points):
            # Sum Reno flows
            for flow in reno_flows:
                if t < len(flow['throughputs']):
                    reno_total[t_idx] += flow['throughputs'][int(t)]
            
            # Sum BBR flows
            for flow in bbr_flows:
                if t < len(flow['throughputs']):
                    bbr_total[t_idx] += flow['throughputs'][int(t)]
        
        reno_cumulative = np.cumsum(reno_total)
        bbr_cumulative = np.cumsum(bbr_total)
        
        ax2.plot(time_points, reno_cumulative, 'b-', linewidth=2, label='TCP Reno (Total)')
        ax2.plot(time_points, bbr_cumulative, 'r-', linewidth=2, label='TCP BBR (Total)')
        ax2.set_ylabel('Cumulative Throughput (Mb)')
        ax2.set_title('Cumulative Data Transferred (Winner Analysis)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Advantage over time
        advantage = bbr_total - reno_total
        colors_adv = ['red' if x > 0 else 'blue' for x in advantage]
        ax3.bar(time_points, advantage, color=colors_adv, alpha=0.7, width=0.8)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax3.set_ylabel('Advantage (Mbps)')
        ax3.set_xlabel('Time (seconds)')
        ax3.set_title('Instantaneous Advantage (Red=BBR wins, Blue=Reno wins)')
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'competition_timeline.png'), dpi=300, bbox_inches='tight')
    plt.show()

def create_competition_dashboard(results_dir):
    """Create comprehensive dashboard showing the competition."""
    
    # Load results
    results_file = os.path.join(results_dir, 'competition_results.json')
    if not os.path.exists(results_file):
        print("Erro: Arquivo de resultados não encontrado")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Create dashboard
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('TCP Competition Dashboard', fontsize=20, fontweight='bold')
    
    # 1. Throughput comparison (top-left)
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Separate flows by algorithm
    reno_flows = {k: v for k, v in results.items() if 'reno' in k.lower() and 'flow' in k}
    bbr_flows = {k: v for k, v in results.items() if 'bbr' in k.lower() and 'flow' in k}
    
    if reno_flows or bbr_flows:
        # Calculate total throughput for each algorithm
        reno_total = sum(flow['avg_throughput'] for flow in reno_flows.values())
        bbr_total = sum(flow['avg_throughput'] for flow in bbr_flows.values())
        
        algorithms = ['TCP Reno', 'TCP BBR']
        throughputs = [reno_total, bbr_total]
        colors = ['#3498db', '#e74c3c']
        
        bars = ax1.bar(algorithms, throughputs, color=colors, alpha=0.8)
        ax1.set_ylabel('Total Throughput (Mbps)')
        ax1.set_title('🏆 Throughput Battle')
        
        # Add value labels
        for bar, val in zip(bars, throughputs):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Show winner
        winner_idx = np.argmax(throughputs)
        bars[winner_idx].set_edgecolor('gold')
        bars[winner_idx].set_linewidth(3)
    
    # 2. Individual flows comparison (top-center)
    ax2 = fig.add_subplot(gs[0, 1])
    
    all_flows = {**reno_flows, **bbr_flows}
    if all_flows:
        flow_names = list(all_flows.keys())
        flow_throughputs = [all_flows[name]['avg_throughput'] for name in flow_names]
        flow_colors = ['blue' if 'reno' in name.lower() else 'red' for name in flow_names]
        
        bars = ax2.bar(range(len(flow_names)), flow_throughputs, color=flow_colors, alpha=0.7)
        ax2.set_ylabel('Throughput (Mbps)')
        ax2.set_title('Individual Flows')
        ax2.set_xticks(range(len(flow_names)))
        ax2.set_xticklabels([name.replace('_flow', '') for name in flow_names], rotation=45)
        
        # Add value labels
        for bar, val in zip(bars, flow_throughputs):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=8)
    
    # 3. Algorithm summary (top-right)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    
    # Create summary text
    summary_text = "🏁 COMPETITION SUMMARY\n\n"
    
    if reno_flows and bbr_flows:
        reno_total = sum(flow['avg_throughput'] for flow in reno_flows.values())
        bbr_total = sum(flow['avg_throughput'] for flow in bbr_flows.values())
        
        winner = "TCP BBR" if bbr_total > reno_total else "TCP Reno"
        advantage = abs(bbr_total - reno_total) / min(reno_total, bbr_total) * 100
        
        summary_text += f"🏆 Winner: {winner}\n"
        summary_text += f"📊 Advantage: {advantage:.1f}%\n\n"
        summary_text += f"🔵 TCP Reno: {len(reno_flows)} flows, {reno_total:.1f} Mbps\n"
        summary_text += f"🔴 TCP BBR: {len(bbr_flows)} flows, {bbr_total:.1f} Mbps\n\n"
        
        # Calculate per-flow averages
        reno_avg = reno_total / len(reno_flows) if reno_flows else 0
        bbr_avg = bbr_total / len(bbr_flows) if bbr_flows else 0
        
        summary_text += f"Per-flow averages:\n"
        summary_text += f"🔵 Reno: {reno_avg:.1f} Mbps/flow\n"
        summary_text += f"🔴 BBR: {bbr_avg:.1f} Mbps/flow\n"
    
    ax3.text(0.05, 0.95, summary_text, transform=ax3.transAxes, 
             verticalalignment='top', fontsize=10, 
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    # 4. Fairness analysis (middle-left)
    ax4 = fig.add_subplot(gs[1, 0])
    
    if 'fairness_index' in results:
        fairness = results['fairness_index']
        
        # Create fairness gauge
        theta = np.linspace(0, np.pi, 100)
        r = 1
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        ax4.plot(x, y, 'k-', linewidth=2)
        ax4.fill_between(x, 0, y, alpha=0.3, color='lightgray')
        
        # Add fairness indicator
        fairness_angle = fairness * np.pi
        ax4.plot([0, np.cos(fairness_angle)], [0, np.sin(fairness_angle)], 
                'r-', linewidth=4, label=f'Fairness: {fairness:.3f}')
        
        ax4.set_xlim(-1.2, 1.2)
        ax4.set_ylim(-0.2, 1.2)
        ax4.set_aspect('equal')
        ax4.set_title('⚖️ Fairness Index')
        ax4.text(0, -0.1, f'{fairness:.3f}', ha='center', fontsize=12, fontweight='bold')
        ax4.set_xticks([])
        ax4.set_yticks([])
    
    # 5. Timeline plot (middle-center and right)
    ax5 = fig.add_subplot(gs[1, 1:])
    
    # Parse timeline data for dashboard
    flow_data = {}
    for file in os.listdir(results_dir):
        if file.endswith('_output.txt'):
            flow_name = file.replace('_output.txt', '')
            times, throughputs = parse_iperf_timeline(os.path.join(results_dir, file))
            if times and throughputs:
                flow_data[flow_name] = {'times': times, 'throughputs': throughputs}
    
    if flow_data:
        for flow_name, data in flow_data.items():
            if 'reno' in flow_name.lower():
                color = 'blue'
                alpha = 0.7
            elif 'bbr' in flow_name.lower():
                color = 'red'
                alpha = 0.7
            else:
                color = 'green'
                alpha = 0.7
            
            ax5.plot(data['times'], data['throughputs'], color=color, linewidth=1.5, 
                    label=flow_name, alpha=alpha)
        
        ax5.set_ylabel('Throughput (Mbps)')
        ax5.set_xlabel('Time (seconds)')
        ax5.set_title('⚡ Real-time Competition')
        ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax5.grid(True, alpha=0.3)
    
    # 6. Queue analysis (bottom row)
    ax6 = fig.add_subplot(gs[2, :])
    
    # Parse queue data
    def parse_queue_simple(file_path):
        times, queues = [], []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        try:
                            times.append(float(parts[0]))
                            queues.append(int(parts[1]))
                        except:
                            continue
        return times, queues
    
    queue_times, queue_lengths = parse_queue_simple(os.path.join(results_dir, 'queue.txt'))
    
    if queue_times and queue_lengths:
        # Convert to relative time
        start_time = min(queue_times)
        relative_times = [(t - start_time) for t in queue_times]
        
        ax6.plot(relative_times, queue_lengths, 'g-', linewidth=2, alpha=0.8)
        ax6.fill_between(relative_times, queue_lengths, alpha=0.3, color='green')
        ax6.set_xlabel('Time (seconds)')
        ax6.set_ylabel('Queue Length (packets)')
        ax6.set_title('📈 Queue Occupancy Over Time')
        ax6.grid(True, alpha=0.3)
        
        # Add queue utilization info
        avg_queue = np.mean(queue_lengths)
        max_queue = np.max(queue_lengths)
        ax6.text(0.02, 0.98, f'Avg: {avg_queue:.1f} packets\nMax: {max_queue} packets', 
                transform=ax6.transAxes, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'competition_dashboard.png'), dpi=300, bbox_inches='tight')
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Visualizar competição TCP")
    parser.add_argument('--dir', '-d', required=True, help="Diretório de resultados")
    parser.add_argument('--type', '-t', choices=['timeline', 'dashboard'], 
                       default='dashboard', help="Tipo de visualização")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"Erro: Diretório não encontrado: {args.dir}")
        sys.exit(1)
    
    print(f"Criando visualização: {args.type}")
    
    if args.type == 'timeline':
        create_competition_timeline_plot(args.dir)
    elif args.type == 'dashboard':
        create_competition_dashboard(args.dir)
    
    print("Visualização concluída!")

if __name__ == "__main__":
    main()