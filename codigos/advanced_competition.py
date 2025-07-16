#!/usr/bin/env python

"""
Advanced TCP Competition Scenarios
Implements various competition scenarios between TCP algorithms
"""

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser
import sys
import os
import json
import numpy as np

from monitor import monitor_qlen

class AdvancedCompetitionTopo(Topo):
    """Advanced topology for multiple TCP flow competition."""
    
    def build(self, num_pairs=2):
        # Create hosts
        hosts = []
        for i in range(num_pairs * 2):
            host = self.addHost(f'h{i+1}')
            hosts.append(host)
        
        # Create switches
        s1 = self.addSwitch('s1')  # Left switch
        s2 = self.addSwitch('s2')  # Right switch
        
        # Connect first half of hosts to left switch (senders)
        for i in range(num_pairs):
            self.addLink(hosts[i], s1, bw=1000, delay='1ms')
        
        # Connect second half to right switch (receivers)
        for i in range(num_pairs, num_pairs * 2):
            self.addLink(s2, hosts[i], bw=1000, delay='1ms')
        
        # Bottleneck link
        self.addLink(s1, s2, bw=10, delay='50ms', max_queue_size=100)

def set_tcp_algorithm(host, algorithm):
    """Set TCP congestion control algorithm."""
    host.cmd(f"sysctl -w net.ipv4.tcp_congestion_control={algorithm}")

def run_scenario_1():
    """Scenario 1: Single Reno vs Single BBR"""
    print("Executando Cenário 1: TCP Reno vs TCP BBR (1 vs 1)")
    
    results_dir = "results/scenario1_reno_vs_bbr"
    os.makedirs(results_dir, exist_ok=True)
    
    topo = AdvancedCompetitionTopo(num_pairs=2)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    h1, h2, h3, h4 = net.get('h1'), net.get('h2'), net.get('h3'), net.get('h4')
    
    # Configure TCP algorithms
    set_tcp_algorithm(h1, 'reno')
    set_tcp_algorithm(h2, 'bbr')
    
    # Start monitoring
    qmon = Process(target=monitor_qlen, args=('s1-eth3', 0.1, f'{results_dir}/queue.txt'))
    qmon.start()
    
    # Start iperf servers
    server1 = h3.popen("iperf -s -p 5001")
    server2 = h4.popen("iperf -s -p 5002")
    sleep(1)
    
    # Start clients
    client1 = h1.popen(f"iperf -c {h3.IP()} -p 5001 -t 30 -i 1 > {results_dir}/reno_output.txt", shell=True)
    client2 = h2.popen(f"iperf -c {h4.IP()} -p 5002 -t 30 -i 1 > {results_dir}/bbr_output.txt", shell=True)
    
    # Wait for completion
    client1.wait()
    client2.wait()
    
    # Cleanup
    qmon.terminate()
    server1.terminate()
    server2.terminate()
    net.stop()
    
    return results_dir

def run_scenario_2():
    """Scenario 2: Multiple Reno flows vs Single BBR"""
    print("Executando Cenário 2: Múltiplos TCP Reno vs Single TCP BBR")
    
    results_dir = "results/scenario2_multiple_reno_vs_bbr"
    os.makedirs(results_dir, exist_ok=True)
    
    topo = AdvancedCompetitionTopo(num_pairs=3)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    hosts = [net.get(f'h{i+1}') for i in range(6)]
    
    # Configure TCP algorithms: h1,h2 = Reno, h3 = BBR
    set_tcp_algorithm(hosts[0], 'reno')
    set_tcp_algorithm(hosts[1], 'reno')
    set_tcp_algorithm(hosts[2], 'bbr')
    
    # Start monitoring
    qmon = Process(target=monitor_qlen, args=('s1-eth4', 0.1, f'{results_dir}/queue.txt'))
    qmon.start()
    
    # Start iperf servers
    servers = []
    for i in range(3):
        server = hosts[i+3].popen(f"iperf -s -p {5001+i}")
        servers.append(server)
    sleep(1)
    
    # Start clients
    clients = []
    for i in range(3):
        algo = 'reno' if i < 2 else 'bbr'
        client = hosts[i].popen(f"iperf -c {hosts[i+3].IP()} -p {5001+i} -t 30 -i 1 > {results_dir}/{algo}_flow_{i+1}.txt", shell=True)
        clients.append(client)
    
    # Wait for completion
    for client in clients:
        client.wait()
    
    # Cleanup
    qmon.terminate()
    for server in servers:
        server.terminate()
    net.stop()
    
    return results_dir

def run_scenario_3():
    """Scenario 3: Time-shifted flows"""
    print("Executando Cenário 3: Fluxos com início em tempos diferentes")
    
    results_dir = "results/scenario3_time_shifted"
    os.makedirs(results_dir, exist_ok=True)
    
    topo = AdvancedCompetitionTopo(num_pairs=2)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    h1, h2, h3, h4 = net.get('h1'), net.get('h2'), net.get('h3'), net.get('h4')
    
    # Configure TCP algorithms
    set_tcp_algorithm(h1, 'reno')
    set_tcp_algorithm(h2, 'bbr')
    
    # Start monitoring
    qmon = Process(target=monitor_qlen, args=('s1-eth3', 0.1, f'{results_dir}/queue.txt'))
    qmon.start()
    
    # Start iperf servers
    server1 = h3.popen("iperf -s -p 5001")
    server2 = h4.popen("iperf -s -p 5002")
    sleep(1)
    
    # Start first flow (Reno)
    client1 = h1.popen(f"iperf -c {h3.IP()} -p 5001 -t 40 -i 1 > {results_dir}/reno_output.txt", shell=True)
    
    # Wait 10 seconds, then start second flow (BBR)
    sleep(10)
    client2 = h2.popen(f"iperf -c {h4.IP()} -p 5002 -t 30 -i 1 > {results_dir}/bbr_output.txt", shell=True)
    
    # Wait for completion
    client1.wait()
    client2.wait()
    
    # Cleanup
    qmon.terminate()
    server1.terminate()
    server2.terminate()
    net.stop()
    
    return results_dir

def analyze_scenario_results(results_dir):
    """Analyze and summarize scenario results."""
    print(f"Analisando resultados de {results_dir}")
    
    # Parse all iperf output files
    flows = {}
    for file in os.listdir(results_dir):
        if file.endswith('_output.txt') or file.endswith('.txt'):
            if 'reno' in file or 'bbr' in file:
                flow_name = file.replace('_output.txt', '').replace('.txt', '')
                throughputs = parse_iperf_output(os.path.join(results_dir, file))
                if throughputs:
                    flows[flow_name] = {
                        'throughputs': throughputs,
                        'avg_throughput': np.mean(throughputs),
                        'std_throughput': np.std(throughputs)
                    }
    
    # Calculate metrics
    total_throughput = sum(flow['avg_throughput'] for flow in flows.values())
    
    # Determine winner
    reno_total = sum(flow['avg_throughput'] for name, flow in flows.items() if 'reno' in name)
    bbr_total = sum(flow['avg_throughput'] for name, flow in flows.items() if 'bbr' in name)
    
    results = {
        'flows': flows,
        'total_throughput': total_throughput,
        'reno_total': reno_total,
        'bbr_total': bbr_total,
        'winner': 'TCP Reno' if reno_total > bbr_total else 'TCP BBR',
        'advantage': abs(reno_total - bbr_total) / min(reno_total, bbr_total) * 100
    }
    
    # Save results
    with open(os.path.join(results_dir, 'analysis.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

def parse_iperf_output(file_path):
    """Parse iperf output file to extract throughput values."""
    throughputs = []
    
    if not os.path.exists(file_path):
        return throughputs
    
    with open(file_path, 'r') as f:
        for line in f:
            if 'Mbits/sec' in line and 'sec' in line:
                parts = line.strip().split()
                for i, part in enumerate(parts):
                    if part == 'Mbits/sec' and i > 0:
                        try:
                            throughput = float(parts[i-1])
                            throughputs.append(throughput)
                        except ValueError:
                            continue
    
    return throughputs

def generate_comparison_report():
    """Generate a comprehensive comparison report."""
    
    scenarios = [
        "results/scenario1_reno_vs_bbr",
        "results/scenario2_multiple_reno_vs_bbr",
        "results/scenario3_time_shifted"
    ]
    
    report = []
    report.append("# TCP Competition Analysis Report")
    report.append("=" * 50)
    report.append("")
    
    for scenario_dir in scenarios:
        if os.path.exists(scenario_dir):
            analysis_file = os.path.join(scenario_dir, 'analysis.json')
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r') as f:
                    results = json.load(f)
                
                scenario_name = os.path.basename(scenario_dir)
                report.append(f"## {scenario_name}")
                report.append(f"**Vencedor:** {results['winner']}")
                report.append(f"**Vantagem:** {results['advantage']:.1f}%")
                report.append(f"**Throughput TCP Reno:** {results['reno_total']:.2f} Mbps")
                report.append(f"**Throughput TCP BBR:** {results['bbr_total']:.2f} Mbps")
                report.append(f"**Throughput Total:** {results['total_throughput']:.2f} Mbps")
                report.append("")
    
    # Write report
    with open("results/competition_summary.md", 'w') as f:
        f.write("\n".join(report))
    
    print("Relatório gerado em: results/competition_summary.md")

def main():
    parser = ArgumentParser(description="Advanced TCP Competition Scenarios")
    parser.add_argument('--scenario', type=int, choices=[1, 2, 3], 
                       help="Scenario to run (1=Reno vs BBR, 2=Multiple Reno vs BBR, 3=Time-shifted)")
    parser.add_argument('--all', action='store_true', help="Run all scenarios")
    
    args = parser.parse_args()
    
    if args.all:
        print("Executando todos os cenários...")
        scenarios = [run_scenario_1, run_scenario_2, run_scenario_3]
        for scenario in scenarios:
            results_dir = scenario()
            analyze_scenario_results(results_dir)
        generate_comparison_report()
    
    elif args.scenario == 1:
        results_dir = run_scenario_1()
        analyze_scenario_results(results_dir)
    elif args.scenario == 2:
        results_dir = run_scenario_2()
        analyze_scenario_results(results_dir)
    elif args.scenario == 3:
        results_dir = run_scenario_3()
        analyze_scenario_results(results_dir)
    else:
        print("Especifique um cenário ou use --all")
        print("Cenários disponíveis:")
        print("  1: TCP Reno vs TCP BBR (1 vs 1)")
        print("  2: Múltiplos TCP Reno vs Single TCP BBR")
        print("  3: Fluxos com início em tempos diferentes")

if __name__ == "__main__":
    main()
