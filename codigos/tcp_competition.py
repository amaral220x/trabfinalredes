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
                    help="Competition scenario: reno_vs_bbr, multiple_reno, multiple_bbr",
                    choices=['reno_vs_bbr', 'multiple_reno', 'multiple_bbr'],
                    default='reno_vs_bbr')

args = parser.parse_args()

class CompetitionTopo(Topo):
    """Topology for TCP competition experiments."""
    
    def build(self, n=4):
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
    for flow_name in ['reno_flow', 'bbr_flow']:
        output_file = os.path.join(results_dir, f'{flow_name}_output.txt')
        throughputs = parse_iperf_output(output_file)
        
        if throughputs:
            results[flow_name] = {
                'throughputs': throughputs,
                'avg_throughput': sum(throughputs) / len(throughputs),
                'min_throughput': min(throughputs),
                'max_throughput': max(throughputs),
                'std_throughput': math.sqrt(sum([(x - sum(throughputs)/len(throughputs))**2 for x in throughputs]) / len(throughputs))
            }
    
    # Calculate fairness index (Jain's fairness index)
    if len(results) == 2:
        flows = list(results.keys())
        avg1 = results[flows[0]]['avg_throughput']
        avg2 = results[flows[1]]['avg_throughput']
        
        fairness_index = (avg1 + avg2)**2 / (2 * (avg1**2 + avg2**2))
        results['fairness_index'] = fairness_index
        
        # Determine winner
        if avg1 > avg2:
            results['winner'] = flows[0]
            results['advantage'] = (avg1 - avg2) / avg2 * 100
        else:
            results['winner'] = flows[1]
            results['advantage'] = (avg2 - avg1) / avg1 * 100
    
    return results

def run_competition_experiment():
    """Run the TCP competition experiment."""
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    
    # Create and start network
    topo = CompetitionTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    # Get hosts
    h1 = net.get('h1')  # Reno sender
    h2 = net.get('h2')  # BBR sender
    h3 = net.get('h3')  # Receiver for h1
    h4 = net.get('h4')  # Receiver for h2
    
    print("Network topology:")
    dumpNodeConnections(net.hosts)
    net.pingAll()
    
    # Start queue monitoring
    qmon = Process(target=monitor_qlen, args=('s1-eth3', 0.1, f'{args.dir}/queue.txt'))
    qmon.start()
    
    # Start iperf servers
    server1 = start_iperf_server(h3, port=5001)
    server2 = start_iperf_server(h4, port=5002)
    
    sleep(1)  # Give servers time to start
    
    # Start ping monitoring
    ping1 = start_ping_monitor(h1, h3.IP(), f'{args.dir}/ping_reno.txt')
    ping2 = start_ping_monitor(h2, h4.IP(), f'{args.dir}/ping_bbr.txt')
    
    # Start iperf clients with different congestion control
    client1 = h1.popen(f"iperf -c {h3.IP()} -p 5001 -t {args.time} -i 1 > {args.dir}/reno_flow_output.txt", shell=True)
    set_tcp_congestion_control(h1, 'reno')
    
    client2 = h2.popen(f"iperf -c {h4.IP()} -p 5002 -t {args.time} -i 1 > {args.dir}/bbr_flow_output.txt", shell=True)
    set_tcp_congestion_control(h2, 'bbr')
    
    # Monitor experiment progress
    start_time = time()
    while True:
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print(f"Experiment running... {delta:.1f}s / {args.time}s")
        sleep(2)
    
    # Wait for clients to finish
    client1.wait()
    client2.wait()
    
    # Stop monitoring
    qmon.terminate()
    ping1.terminate()
    ping2.terminate()
    
    # Stop servers
    server1.terminate()
    server2.terminate()
    
    # Analyze results
    results = analyze_competition_results(args.dir)
    
    # Save results
    with open(f'{args.dir}/competition_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print("TCP COMPETITION RESULTS")
    print("="*50)
    
    if 'reno_flow' in results and 'bbr_flow' in results:
        print(f"TCP Reno Average Throughput: {results['reno_flow']['avg_throughput']:.2f} Mbps")
        print(f"TCP BBR Average Throughput: {results['bbr_flow']['avg_throughput']:.2f} Mbps")
        print(f"Fairness Index: {results.get('fairness_index', 'N/A'):.3f}")
        print(f"Winner: {results.get('winner', 'N/A')}")
        print(f"Advantage: {results.get('advantage', 0):.1f}%")
    
    print("\nDetailed metrics saved to:", f'{args.dir}/competition_results.json')
    
    net.stop()
    
    # Clean up any remaining processes
    Popen("pkill -f iperf", shell=True).wait()

if __name__ == "__main__":
    run_competition_experiment()
