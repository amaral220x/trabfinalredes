#!/usr/bin/env python

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser
import sys
import os
import math
import json

from monitor import monitor_qlen

parser = ArgumentParser(description="TCP Competition: Reno vs BBR")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=30)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

parser.add_argument('--scenario',
                    help="Competition scenario",
                    choices=['reno_vs_bbr', '2reno_vs_2bbr', '2reno_vs_1bbr', 'multiple_reno', 'multiple_bbr'],
                    default='reno_vs_bbr')

args = parser.parse_args()

class CompetitionTopo(Topo):
    """Topology for TCP competition experiments."""
    
    def build(self, scenario='reno_vs_bbr'):
        if scenario == 'reno_vs_bbr':
            self.build_1v1()
        elif scenario == '2reno_vs_2bbr':
            self.build_2v2()
        elif scenario == '2reno_vs_1bbr':
            self.build_2v1()
        else:
            self.build_1v1()  # Default
    
    def build_1v1(self):
        """Build 1 Reno vs 1 BBR topology."""
        # Create hosts
        h1 = self.addHost('h1')  # Reno sender
        h2 = self.addHost('h2')  # BBR sender  
        h3 = self.addHost('h3')  # Receiver for h1
        h4 = self.addHost('h4')  # Receiver for h2
        
        # Create switches
        s1 = self.addSwitch('s1')  # Left switch
        s2 = self.addSwitch('s2')  # Right switch
        
        # Links from senders to left switch (high bandwidth)
        self.addLink(h1, s1, bw=args.bw_host, delay='1ms')
        self.addLink(h2, s1, bw=args.bw_host, delay='1ms')
        
        # Bottleneck link between switches
        self.addLink(s1, s2, 
                     bw=args.bw_net, 
                     delay='%fms' % args.delay, 
                     max_queue_size=args.maxq)
        
        # Links from right switch to receivers (high bandwidth)
        self.addLink(s2, h3, bw=args.bw_host, delay='1ms')
        self.addLink(s2, h4, bw=args.bw_host, delay='1ms')
    
    def build_2v2(self):
        """Build 2 Reno vs 2 BBR topology."""
        # Create hosts
        h1 = self.addHost('h1')  # Reno sender 1
        h2 = self.addHost('h2')  # Reno sender 2
        h3 = self.addHost('h3')  # BBR sender 1
        h4 = self.addHost('h4')  # BBR sender 2
        h5 = self.addHost('h5')  # Receiver for h1
        h6 = self.addHost('h6')  # Receiver for h2
        h7 = self.addHost('h7')  # Receiver for h3
        h8 = self.addHost('h8')  # Receiver for h4
        
        # Create switches
        s1 = self.addSwitch('s1')  # Left switch
        s2 = self.addSwitch('s2')  # Right switch
        
        # Links from senders to left switch
        self.addLink(h1, s1, bw=args.bw_host, delay='1ms')
        self.addLink(h2, s1, bw=args.bw_host, delay='1ms')
        self.addLink(h3, s1, bw=args.bw_host, delay='1ms')
        self.addLink(h4, s1, bw=args.bw_host, delay='1ms')
        
        # Bottleneck link between switches
        self.addLink(s1, s2, 
                     bw=args.bw_net, 
                     delay='%fms' % args.delay, 
                     max_queue_size=args.maxq)
        
        # Links from right switch to receivers
        self.addLink(s2, h5, bw=args.bw_host, delay='1ms')
        self.addLink(s2, h6, bw=args.bw_host, delay='1ms')
        self.addLink(s2, h7, bw=args.bw_host, delay='1ms')
        self.addLink(s2, h8, bw=args.bw_host, delay='1ms')
    
    def build_2v1(self):
        """Build 2 Reno vs 1 BBR topology."""
        # Create hosts
        h1 = self.addHost('h1')  # Reno sender 1
        h2 = self.addHost('h2')  # Reno sender 2
        h3 = self.addHost('h3')  # BBR sender
        h4 = self.addHost('h4')  # Receiver for h1
        h5 = self.addHost('h5')  # Receiver for h2
        h6 = self.addHost('h6')  # Receiver for h3
        
        # Create switches
        s1 = self.addSwitch('s1')  # Left switch
        s2 = self.addSwitch('s2')  # Right switch
        
        # Links from senders to left switch
        self.addLink(h1, s1, bw=args.bw_host, delay='1ms')
        self.addLink(h2, s1, bw=args.bw_host, delay='1ms')
        self.addLink(h3, s1, bw=args.bw_host, delay='1ms')
        
        # Bottleneck link between switches
        self.addLink(s1, s2, 
                     bw=args.bw_net, 
                     delay='%fms' % args.delay, 
                     max_queue_size=args.maxq)
        
        # Links from right switch to receivers
        self.addLink(s2, h4, bw=args.bw_host, delay='1ms')
        self.addLink(s2, h5, bw=args.bw_host, delay='1ms')
        self.addLink(s2, h6, bw=args.bw_host, delay='1ms')

def set_tcp_congestion_control(host, algorithm):
    """Set TCP congestion control algorithm on a host."""
    host.cmd(f"sysctl -w net.ipv4.tcp_congestion_control={algorithm}")

def start_iperf_server(host, port=5001):
    """Start iperf server on a host."""
    print(f"Starting iperf server on {host.name} port {port}")
    return host.popen(f"iperf -s -p {port} -i 1")

def start_iperf_client(host, server_ip, port=5001, duration=30, congestion_control=None):
    """Start iperf client with specific congestion control."""
    if congestion_control:
        set_tcp_congestion_control(host, congestion_control)
    
    print(f"Starting iperf client on {host.name} to {server_ip}:{port} with {congestion_control}")
    return host.popen(f"iperf -c {server_ip} -p {port} -t {duration} -i 1")

def start_ping_monitor(host, target_ip, outfile):
    """Start continuous ping monitoring."""
    print(f"Starting ping from {host.name} to {target_ip}")
    ping_cmd = f"ping -i 0.1 -c {args.time * 10} {target_ip} > {outfile}"
    return host.popen(ping_cmd, shell=True)

def parse_iperf_output(output_file):
    """Parse iperf output to extract throughput and other metrics."""
    if not os.path.exists(output_file):
        return None
    
    with open(output_file, 'r') as f:
        lines = f.readlines()
    
    throughputs = []
    for line in lines:
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

def analyze_competition_results(results_dir):
    """Analyze competition results and determine winner."""
    results = {}
    
    # Parse iperf results for each flow
    for file in os.listdir(results_dir):
        if file.endswith('_output.txt'):
            flow_name = file.replace('_output.txt', '')
            throughputs = parse_iperf_output(os.path.join(results_dir, file))
            
            if throughputs:
                results[flow_name] = {
                    'throughputs': throughputs,
                    'avg_throughput': sum(throughputs) / len(throughputs),
                    'min_throughput': min(throughputs),
                    'max_throughput': max(throughputs),
                    'std_throughput': math.sqrt(sum([(x - sum(throughputs)/len(throughputs))**2 for x in throughputs]) / len(throughputs))
                }
    
    # Separate flows by algorithm
    reno_flows = {k: v for k, v in results.items() if 'reno' in k.lower()}
    bbr_flows = {k: v for k, v in results.items() if 'bbr' in k.lower()}
    
    if reno_flows and bbr_flows:
        # Calculate total throughput for each algorithm
        reno_total = sum(flow['avg_throughput'] for flow in reno_flows.values())
        bbr_total = sum(flow['avg_throughput'] for flow in bbr_flows.values())
        
        # Calculate fairness index (modified for multiple flows)
        all_throughputs = [flow['avg_throughput'] for flow in results.values()]
        n = len(all_throughputs)
        if n > 0:
            sum_throughputs = sum(all_throughputs)
            sum_squared_throughputs = sum(x**2 for x in all_throughputs)
            fairness_index = (sum_throughputs**2) / (n * sum_squared_throughputs)
        else:
            fairness_index = 0
        
        results['fairness_index'] = fairness_index
        
        # Determine winner
        if reno_total > bbr_total:
            results['winner'] = 'TCP Reno'
            results['advantage'] = (reno_total - bbr_total) / bbr_total * 100
        else:
            results['winner'] = 'TCP BBR'
            results['advantage'] = (bbr_total - reno_total) / reno_total * 100
        
        # Additional statistics
        results['reno_total'] = reno_total
        results['bbr_total'] = bbr_total
        results['reno_flows_count'] = len(reno_flows)
        results['bbr_flows_count'] = len(bbr_flows)
        results['reno_avg_per_flow'] = reno_total / len(reno_flows)
        results['bbr_avg_per_flow'] = bbr_total / len(bbr_flows)
    
    return results

def run_competition_experiment():
    """Run the TCP competition experiment."""
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    
    # Create and start network
    topo = CompetitionTopo(scenario=args.scenario)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    print("Network topology:")
    dumpNodeConnections(net.hosts)
    net.pingAll()
    
    # Start queue monitoring
    qmon = Process(target=monitor_qlen, args=('s1-eth5', 0.1, f'{args.dir}/queue.txt'))
    qmon.start()
    
    # Run experiment based on scenario
    if args.scenario == 'reno_vs_bbr':
        run_1v1_experiment(net)
    elif args.scenario == '2reno_vs_2bbr':
        run_2v2_experiment(net)
    elif args.scenario == '2reno_vs_1bbr':
        run_2v1_experiment(net)
    
    # Stop monitoring
    qmon.terminate()
    
    # Analyze results
    results = analyze_competition_results(args.dir)
    
    # Save results
    with open(f'{args.dir}/competition_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print_results_summary(results)
    
    net.stop()
    
    # Clean up any remaining processes
    Popen("pkill -f iperf", shell=True).wait()

def run_1v1_experiment(net):
    """Run 1 Reno vs 1 BBR experiment."""
    h1 = net.get('h1')  # Reno sender
    h2 = net.get('h2')  # BBR sender
    h3 = net.get('h3')  # Receiver for h1
    h4 = net.get('h4')  # Receiver for h2
    
    # Configure TCP algorithms
    set_tcp_congestion_control(h1, 'reno')
    set_tcp_congestion_control(h2, 'bbr')
    
    # Start iperf servers
    server1 = start_iperf_server(h3, port=5001)
    server2 = start_iperf_server(h4, port=5002)
    
    sleep(1)  # Give servers time to start
    
    # Start ping monitoring
    ping1 = start_ping_monitor(h1, h3.IP(), f'{args.dir}/ping_reno.txt')
    ping2 = start_ping_monitor(h2, h4.IP(), f'{args.dir}/ping_bbr.txt')
    
    # Start iperf clients
    client1 = h1.popen(f"iperf -c {h3.IP()} -p 5001 -t {args.time} -i 1 > {args.dir}/reno_flow_output.txt", shell=True)
    client2 = h2.popen(f"iperf -c {h4.IP()} -p 5002 -t {args.time} -i 1 > {args.dir}/bbr_flow_output.txt", shell=True)
    
    # Monitor experiment progress
    monitor_experiment_progress()
    
    # Wait for clients to finish
    client1.wait()
    client2.wait()
    
    # Stop monitoring
    ping1.terminate()
    ping2.terminate()
    
    # Stop servers
    server1.terminate()
    server2.terminate()

def run_2v2_experiment(net):
    """Run 2 Reno vs 2 BBR experiment."""
    h1 = net.get('h1')  # Reno sender 1
    h2 = net.get('h2')  # Reno sender 2
    h3 = net.get('h3')  # BBR sender 1
    h4 = net.get('h4')  # BBR sender 2
    h5 = net.get('h5')  # Receiver for h1
    h6 = net.get('h6')  # Receiver for h2
    h7 = net.get('h7')  # Receiver for h3
    h8 = net.get('h8')  # Receiver for h4
    
    # Configure TCP algorithms
    set_tcp_congestion_control(h1, 'reno')
    set_tcp_congestion_control(h2, 'reno')
    set_tcp_congestion_control(h3, 'bbr')
    set_tcp_congestion_control(h4, 'bbr')
    
    # Start iperf servers
    server1 = start_iperf_server(h5, port=5001)
    server2 = start_iperf_server(h6, port=5002)
    server3 = start_iperf_server(h7, port=5003)
    server4 = start_iperf_server(h8, port=5004)
    
    sleep(1)
    
    # Start ping monitoring (sample from each algorithm)
    ping1 = start_ping_monitor(h1, h5.IP(), f'{args.dir}/ping_reno_1.txt')
    ping2 = start_ping_monitor(h3, h7.IP(), f'{args.dir}/ping_bbr_1.txt')
    
    # Start iperf clients
    client1 = h1.popen(f"iperf -c {h5.IP()} -p 5001 -t {args.time} -i 1 > {args.dir}/reno_flow_1_output.txt", shell=True)
    client2 = h2.popen(f"iperf -c {h6.IP()} -p 5002 -t {args.time} -i 1 > {args.dir}/reno_flow_2_output.txt", shell=True)
    client3 = h3.popen(f"iperf -c {h7.IP()} -p 5003 -t {args.time} -i 1 > {args.dir}/bbr_flow_1_output.txt", shell=True)
    client4 = h4.popen(f"iperf -c {h8.IP()} -p 5004 -t {args.time} -i 1 > {args.dir}/bbr_flow_2_output.txt", shell=True)
    
    # Monitor experiment progress
    monitor_experiment_progress()
    
    # Wait for clients to finish
    client1.wait()
    client2.wait()
    client3.wait()
    client4.wait()
    
    # Stop monitoring
    ping1.terminate()
    ping2.terminate()
    
    # Stop servers
    server1.terminate()
    server2.terminate()
    server3.terminate()
    server4.terminate()

def run_2v1_experiment(net):
    """Run 2 Reno vs 1 BBR experiment."""
    h1 = net.get('h1')  # Reno sender 1
    h2 = net.get('h2')  # Reno sender 2
    h3 = net.get('h3')  # BBR sender
    h4 = net.get('h4')  # Receiver for h1
    h5 = net.get('h5')  # Receiver for h2
    h6 = net.get('h6')  # Receiver for h3
    
    # Configure TCP algorithms
    set_tcp_congestion_control(h1, 'reno')
    set_tcp_congestion_control(h2, 'reno')
    set_tcp_congestion_control(h3, 'bbr')
    
    # Start iperf servers
    server1 = start_iperf_server(h4, port=5001)
    server2 = start_iperf_server(h5, port=5002)
    server3 = start_iperf_server(h6, port=5003)
    
    sleep(1)
    
    # Start ping monitoring
    ping1 = start_ping_monitor(h1, h4.IP(), f'{args.dir}/ping_reno_1.txt')
    ping2 = start_ping_monitor(h2, h5.IP(), f'{args.dir}/ping_reno_2.txt')
    ping3 = start_ping_monitor(h3, h6.IP(), f'{args.dir}/ping_bbr.txt')
    
    # Start iperf clients
    client1 = h1.popen(f"iperf -c {h4.IP()} -p 5001 -t {args.time} -i 1 > {args.dir}/reno_flow_1_output.txt", shell=True)
    client2 = h2.popen(f"iperf -c {h5.IP()} -p 5002 -t {args.time} -i 1 > {args.dir}/reno_flow_2_output.txt", shell=True)
    client3 = h3.popen(f"iperf -c {h6.IP()} -p 5003 -t {args.time} -i 1 > {args.dir}/bbr_flow_output.txt", shell=True)
    
    # Monitor experiment progress
    monitor_experiment_progress()
    
    # Wait for clients to finish
    client1.wait()
    client2.wait()
    client3.wait()
    
    # Stop monitoring
    ping1.terminate()
    ping2.terminate()
    ping3.terminate()
    
    # Stop servers
    server1.terminate()
    server2.terminate()
    server3.terminate()

def monitor_experiment_progress():
    """Monitor and display experiment progress."""
    start_time = time()
    while True:
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print(f"Experiment running... {delta:.1f}s / {args.time}s")
        sleep(2)

def print_results_summary(results):
    """Print summary of competition results."""
    print("\n" + "="*50)
    print("TCP COMPETITION RESULTS")
    print("="*50)
    
    # Count flows by algorithm
    reno_flows = [k for k in results.keys() if 'reno' in k.lower() and 'flow' in k]
    bbr_flows = [k for k in results.keys() if 'bbr' in k.lower() and 'flow' in k]
    
    if reno_flows and bbr_flows:
        # Calculate totals
        reno_total = sum(results[flow]['avg_throughput'] for flow in reno_flows)
        bbr_total = sum(results[flow]['avg_throughput'] for flow in bbr_flows)
        
        print(f"Scenario: {args.scenario}")
        print(f"TCP Reno flows: {len(reno_flows)}")
        print(f"TCP BBR flows: {len(bbr_flows)}")
        print(f"TCP Reno Total Throughput: {reno_total:.2f} Mbps")
        print(f"TCP BBR Total Throughput: {bbr_total:.2f} Mbps")
        
        # Determine winner
        if reno_total > bbr_total:
            winner = "TCP Reno"
            advantage = (reno_total - bbr_total) / bbr_total * 100
        else:
            winner = "TCP BBR"
            advantage = (bbr_total - reno_total) / reno_total * 100
        
        print(f"Winner: {winner}")
        print(f"Advantage: {advantage:.1f}%")
        
        # Per-flow averages
        reno_avg = reno_total / len(reno_flows)
        bbr_avg = bbr_total / len(bbr_flows)
        print(f"TCP Reno Average per flow: {reno_avg:.2f} Mbps")
        print(f"TCP BBR Average per flow: {bbr_avg:.2f} Mbps")
        
        # Fairness analysis
        if 'fairness_index' in results:
            print(f"Fairness Index: {results['fairness_index']:.3f}")
    
    print("\nDetailed metrics saved to:", f'{args.dir}/competition_results.json')

if __name__ == "__main__":
    run_competition_experiment()
