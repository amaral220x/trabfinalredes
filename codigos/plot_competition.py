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
    
    # Parse data
    reno_times, reno_throughputs = parse_iperf_timeline(os.path.join(results_dir, 'reno_flow_output.txt'))
    bbr_times, bbr_throughputs = parse_iperf_timeline(os.path.join(results_dir, 'bbr_flow_output.txt'))
    
    if not reno_times or not bbr_times:
        print("Erro: Dados de throughput não encontrados")
        return
    
    # Create figure
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('TCP Competition Timeline: Reno vs BBR', fontsize=16, fontweight='bold')
    
    # Plot 1: Throughput over time
    ax1.plot(reno_times, reno_throughputs, 'b-', linewidth=2, label='TCP Reno', marker='o', markersize=4)
    ax1.plot(bbr_times, bbr_throughputs, 'r-', linewidth=2, label='TCP BBR', marker='s', markersize=4)
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Throughput Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cumulative throughput (who's winning)
    reno_cumulative = np.cumsum(reno_throughputs)
    bbr_cumulative = np.cumsum(bbr_throughputs)
    
    ax2.plot(reno_times, reno_cumulative, 'b-', linewidth=2, label='TCP Reno (Cumulative)')
    ax2.plot(bbr_times, bbr_cumulative, 'r-', linewidth=2, label='TCP BBR (Cumulative)')
    ax2.set_ylabel('Cumulative Throughput (Mb)')
    ax2.set_title('Cumulative Data Transferred (Winner Analysis)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Advantage over time
    min_len = min(len(reno_throughputs), len(bbr_throughputs))
    advantage = []
    advantage_times = []
    
    for i in range(min_len):
        if i < len(reno_times) and i < len(bbr_times):
            adv = bbr_throughputs[i] - reno_throughputs[i]
            advantage.append(adv)
            advantage_times.append((reno_times[i] + bbr_times[i]) / 2)
    
    colors = ['red' if x > 0 else 'blue' for x in advantage]
    ax3.bar(advantage_times, advantage, color=colors, alpha=0.7, width=0.8)
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
    fig.suptitle('TCP Competition Dashboard: Reno vs BBR', fontsize=20, fontweight='bold')
    
    # 1. Throughput comparison (top-left)
    ax1 = fig.add_subplot(gs[0, 0])
    if 'reno_flow' in results and 'bbr_flow' in results:
        algorithms = ['TCP Reno', 'TCP BBR']
        throughputs = [results['reno_flow']['avg_throughput'], 
                      results['bbr_flow']['avg_throughput']]
        colors = ['#3498db', '#e74c3c']
        
        bars = ax1.bar(algorithms, throughputs, color=colors, alpha=0.8)
        ax1.set_ylabel('Avg Throughput (Mbps)')
        ax1.set_title('🏆 Throughput Battle')
        
        # Add value labels
        for bar, val in zip(bars, throughputs):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Show winner
        winner_idx = np.argmax(throughputs)
        bars[winner_idx].set_edgecolor('gold')
        bars[winner_idx].set_linewidth(3)
    
    # 2. Timeline plot (top-center and top-right)
    ax2 = fig.add_subplot(gs[0, 1:])
    reno_times, reno_throughputs = parse_iperf_timeline(os.path.join(results_dir, 'reno_flow_output.txt'))
    bbr_times, bbr_throughputs = parse_iperf_timeline(os.path.join(results_dir, 'bbr_flow_output.txt'))
    
    if reno_times and bbr_times:
        ax2.plot(reno_times, reno_throughputs, 'b-', linewidth=2, label='TCP Reno', marker='o', markersize=3)
        ax2.plot(bbr_times, bbr_throughputs, 'r-', linewidth=2, label='TCP BBR', marker='s', markersize=3)
        ax2.set_ylabel('Throughput (Mbps)')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_title('⚡ Real-time Competition')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # 3. Fairness analysis (middle-left)
    ax3 = fig.add_subplot(gs[1, 0])
    if 'fairness_index' in results:
        fairness = results['fairness_index']
        
        # Create fairness gauge
        theta = np.linspace(0, np.pi, 100)
        r = 1
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        ax3.plot(x, y, 'k-', linewidth=2)
        ax3.fill_between(x, 0, y, alpha=0.3, color='lightgray')
        
        # Add fairness indicator
        fairness_angle = fairness * np.pi
        ax3.plot([0, np.cos(fairness_angle)], [0, np.sin(fairness_angle)], 
                'r-', linewidth=4, label=f'Fairness: {fairness:.3f}')
        
        ax3.set_xlim(-1.2, 1.2)
        ax3.set_ylim(-0.2, 1.2)
        ax3.set_aspect('equal')
        ax3.set_title('⚖️ Fairness Index')
        ax3.text(0, -0.1, f'{fairness:.3f}', ha='center', fontsize=12, fontweight='bold')
        ax3.set_xticks([])
        ax3.set_yticks([])
    
    # 4. RTT comparison (middle-center)
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Parse RTT data
    def parse_ping_simple(file_path):
        rtts = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    if 'time=' in line:
                        try:
                            rtt = float(line.split('time=')[1].split()[0])
                            rtts.append(rtt)
                        except:
                            continue
        return rtts
    
    reno_rtts = parse_ping_simple(os.path.join(results_dir, 'ping_reno.txt'))
    bbr_rtts = parse_ping_simple(os.path.join(results_dir, 'ping_bbr.txt'))
    
    if reno_rtts and bbr_rtts:
        data = [reno_rtts, bbr_rtts]
        labels = ['TCP Reno', 'TCP BBR']
        
        box_plot = ax4.boxplot(data, labels=labels, patch_artist=True)
        colors = ['#3498db', '#e74c3c']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax4.set_ylabel('RTT (ms)')
        ax4.set_title('📡 Latency Comparison')
        ax4.grid(True, alpha=0.3)
    
    # 5. Competition summary (middle-right)
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    
    # Create summary text
    summary_text = "🏁 COMPETITION SUMMARY\n\n"
    
    if 'winner' in results:
        summary_text += f"🏆 Winner: {results['winner']}\n"
        summary_text += f"📊 Advantage: {results.get('advantage', 0):.1f}%\n\n"
    
    if 'reno_flow' in results and 'bbr_flow' in results:
        summary_text += f"🔵 TCP Reno: {results['reno_flow']['avg_throughput']:.1f} Mbps\n"
        summary_text += f"🔴 TCP BBR: {results['bbr_flow']['avg_throughput']:.1f} Mbps\n\n"
    
    if 'fairness_index' in results:
        fairness_desc = "Excellent" if results['fairness_index'] >= 0.9 else \
                       "Good" if results['fairness_index'] >= 0.7 else \
                       "Moderate" if results['fairness_index'] >= 0.5 else "Poor"
        summary_text += f"⚖️ Fairness: {fairness_desc}\n"
    
    ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes, 
             verticalalignment='top', fontsize=11, 
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
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
    
    plt.savefig(os.path.join(results_dir, 'competition_dashboard.png'), dpi=300, bbox_inches='tight')
    plt.show()

def create_animated_competition(results_dir):
    """Create animated plot showing competition evolution."""
    
    # Parse data
    reno_times, reno_throughputs = parse_iperf_timeline(os.path.join(results_dir, 'reno_flow_output.txt'))
    bbr_times, bbr_throughputs = parse_iperf_timeline(os.path.join(results_dir, 'bbr_flow_output.txt'))
    
    if not reno_times or not bbr_times:
        print("Erro: Dados insuficientes para animação")
        return
    
    # Setup animation
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle('TCP Competition Animation', fontsize=16)
    
    # Initialize plots
    line1, = ax1.plot([], [], 'b-', linewidth=2, label='TCP Reno')
    line2, = ax1.plot([], [], 'r-', linewidth=2, label='TCP BBR')
    ax1.set_xlim(0, max(max(reno_times), max(bbr_times)))
    ax1.set_ylim(0, max(max(reno_throughputs), max(bbr_throughputs)) * 1.1)
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Real-time Throughput')
    ax1.legend()
    ax1.grid(True)
    
    # Score tracker
    score_text = ax2.text(0.5, 0.5, '', transform=ax2.transAxes, 
                         ha='center', va='center', fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')
    
    def animate(frame):
        # Update throughput lines
        if frame < len(reno_times):
            line1.set_data(reno_times[:frame+1], reno_throughputs[:frame+1])
        if frame < len(bbr_times):
            line2.set_data(bbr_times[:frame+1], bbr_throughputs[:frame+1])
        
        # Update score
        if frame < min(len(reno_throughputs), len(bbr_throughputs)):
            reno_total = sum(reno_throughputs[:frame+1])
            bbr_total = sum(bbr_throughputs[:frame+1])
            
            if reno_total > bbr_total:
                leader = "TCP Reno"
                score_color = "blue"
            else:
                leader = "TCP BBR"
                score_color = "red"
            
            score_text.set_text(f"Current Leader: {leader}\n"
                               f"Reno Total: {reno_total:.1f} Mb\n"
                               f"BBR Total: {bbr_total:.1f} Mb")
            score_text.set_color(score_color)
        
        return line1, line2, score_text
    
    # Create animation
    anim = animation.FuncAnimation(fig, animate, frames=max(len(reno_times), len(bbr_times)),
                                 interval=200, blit=True, repeat=True)
    
    plt.tight_layout()
    plt.show()
    
    # Save animation
    # anim.save(os.path.join(results_dir, 'competition_animation.gif'), writer='pillow', fps=5)

def main():
    parser = argparse.ArgumentParser(description="Visualizar competição TCP")
    parser.add_argument('--dir', '-d', required=True, help="Diretório de resultados")
    parser.add_argument('--type', '-t', choices=['timeline', 'dashboard', 'animated'], 
                       default='dashboard', help="Tipo de visualização")
    parser.add_argument('--save', '-s', action='store_true', help="Salvar gráficos")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"Erro: Diretório não encontrado: {args.dir}")
        sys.exit(1)
    
    print(f"Criando visualização: {args.type}")
    
    if args.type == 'timeline':
        create_competition_timeline_plot(args.dir)
    elif args.type == 'dashboard':
        create_competition_dashboard(args.dir)
    elif args.type == 'animated':
        create_animated_competition(args.dir)
    
    print("Visualização concluída!")

if __name__ == "__main__":
    main()
