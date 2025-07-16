# bufferbloat.py (VERSÃO FINAL FUNCIONAL)
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import info
from mininet.util import dumpNodeConnections

from subprocess import Popen
from time import sleep
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen
import os

# --- Argument Parser ---
parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B', type=float, help="Bandwidth of host links (Mb/s)", default=1000)
parser.add_argument('--bw-net', '-b', type=float, help="Bandwidth of bottleneck (Mb/s)", required=True)
parser.add_argument('--delay', type=float, help="Link propagation delay (ms)", required=True)
parser.add_argument('--dir', '-d', help="Directory to store outputs", required=True)
parser.add_argument('--time', '-t', help="Duration (sec) to run the experiment", type=int, default=10)
parser.add_argument('--maxq', type=int, help="Max buffer size of network interface in packets", default=100)
parser.add_argument('--cong', help="Congestion control algorithm to use", default="reno")
parser.add_argument('--bonus', help="Run the competition bonus experiment", action='store_true')
args = parser.parse_args()

# --- Topologia Original (Partes 2 e 3) ---
class BBTopo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        switch = self.addSwitch('s0')
        self.addLink(h1, switch, bw=args.bw_host, delay='%fms' % (args.delay / 2))
        self.addLink(switch, h2, bw=args.bw_net, delay='%fms' % (args.delay / 2), max_queue_size=args.maxq)

# --- Topologia do Bônus ---
class BonusTopo(Topo):
    def build(self):
        h_reno = self.addHost('h_reno')
        r_reno = self.addHost('r_reno')
        h_bbr = self.addHost('h_bbr')
        r_bbr = self.addHost('r_bbr')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        self.addLink(h_reno, s1, bw=1000)
        self.addLink(h_bbr, s1, bw=1000)
        self.addLink(s1, s2, bw=args.bw_net, delay='%fms' % args.delay, max_queue_size=args.maxq)
        self.addLink(s2, r_reno, bw=1000)
        self.addLink(s2, r_bbr, bw=1000)

# --- Função para Monitorar Fila ---
def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen, args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

# --- Experimento Bônus ---
def run_bonus_experiment(net):
    h_reno, r_reno = net.get('h_reno', 'r_reno')
    h_bbr, r_bbr = net.get('h_bbr', 'r_bbr')

    info("Setting congestion control on hosts...\n")
    h_reno.cmd("sysctl -w net.ipv4.tcp_congestion_control=reno")
    h_bbr.cmd("sysctl -w net.ipv4.tcp_congestion_control=bbr")

    info("Starting iperf servers...\n")
    r_reno.cmd("iperf -s -w 16m &")
    r_bbr.cmd("iperf -s -w 16m &")
    sleep(3)

    info("Starting iperf clients...\n")
    h_reno.cmd(f"iperf -c {r_reno.IP()} -t {args.time} -i 1 > {args.dir}/iperf_reno.txt 2>&1 &")
    h_bbr.cmd(f"iperf -c {r_bbr.IP()} -t {args.time} -i 1 > {args.dir}/iperf_bbr.txt 2>&1 &")

    # Espera o tempo total de execução
    sleep(args.time + 2)

    return [], []

# --- Experimento Original (Partes 2 e 3) ---
def run_original_experiment(net):
    h1, h2 = net.get('h1', 'h2')
    h1.cmd(f"iperf -c {h2.IP()} -t {args.time} -i 1 > {args.dir}/iperf_output.txt 2>&1 &")
    h2.cmd("iperf -s -w 16m &")
    sleep(args.time + 2)
    return [], []

# --- Função Principal ---
def main():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    os.system("modprobe tcp_bbr")

    topo = BonusTopo() if args.bonus else BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    dumpNodeConnections(net.hosts)
    net.pingAll()

    qmon = None
    if args.bonus:
        qmon = start_qmon(iface='s1-eth3', outfile=f'{args.dir}/q.txt')
        run_bonus_experiment(net)
    else:
        os.system(f"sysctl -w net.ipv4.tcp_congestion_control={args.cong}")
        qmon = start_qmon(iface='s0-eth2', outfile=f'{args.dir}/q.txt')
        run_original_experiment(net)

    if qmon:
        qmon.terminate()

    net.stop()
    Popen("pgrep -f iperf | xargs kill -9", shell=True).wait()
    info("Experiment finished.\n")

if __name__ == "__main__":
    main()
