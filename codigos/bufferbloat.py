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

from monitor import monitor_qlen

import sys
import os
import math

parser = ArgumentParser(description="Bufferbloat tests")
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
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default that doesn't have the usual sawtooth
# behaviour.  For those who are curious, invoke this script with
# --cong cubic and see what happens...
# sysctl -a | grep cong should list some interesting parameters.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

# Expt parameters
args = parser.parse_args()

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        # TODO: create two hosts
        # Criando os dois hosts h1 e h2
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        # TODO: Add links with appropriate characteristics
        # Adicionando links com características específicas
        # Link h1 -> switch: largura de banda alta (1000 Mb/s), delay baixo
        self.addLink(h1, switch, 
                     bw=args.bw_host, 
                     delay='%fms' % (args.delay/2), 
                     max_queue_size=args.maxq)
        
        # Link switch -> h2: largura de banda baixa (bottleneck), delay baixo
        # Este é o link gargalo que causa o bufferbloat
        self.addLink(switch, h2, 
                     bw=args.bw_net, 
                     delay='%fms' % (args.delay/2), 
                     max_queue_size=args.maxq)

# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!

def start_iperf(net):
    h1 = net.get('h1')
    h2 = net.get('h2')
    print("Starting iperf server...")
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    server = h2.popen("iperf -s -w 16m")

    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    # Iniciando o cliente iperf no h1 para criar um fluxo TCP de longa duração
    # -c especifica o servidor de destino (h2)
    # -t especifica a duração do teste (args.time)
    # -i especifica o intervalo de relatórios
    print("Starting iperf client...")
    client = h1.popen("iperf -c %s -t %d -i 1" % (h2.IP(), args.time))
    return server, client

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_ping(net):
    # TODO: Start a ping train from h1 to h2 (or h2 to h1, does it
    # matter?)  Measure RTTs every 0.1 second.  Read the ping man page
    # to see how to do this.

    # Hint: Use host.popen(cmd, shell=True).  If you pass shell=True
    # to popen, you can redirect cmd's output using shell syntax.
    # i.e. ping ... > /path/to/ping.
    
    # Iniciando ping de h1 para h2
    # -i 0.1 especifica intervalo de 0.1 segundos entre pings (10 amostras/segundo)
    # -c especifica número total de pings (duração * 10)
    h1 = net.get('h1')
    h2 = net.get('h2')
    print("Starting ping from h1 to h2...")
    ping_cmd = "ping -i 0.1 -c %d %s > %s/ping.txt" % (args.time * 10, h2.IP(), args.dir)
    ping = h1.popen(ping_cmd, shell=True)
    return ping

def start_webserver(net):
    h1 = net.get('h1')
    proc = h1.popen("python webserver.py", shell=True)
    sleep(1)
    return [proc]

def measure_webpage_fetch_time(net):
    """
    Mede o tempo de busca da página web usando curl
    Retorna uma lista com os tempos de fetch
    """
    h2 = net.get('h2')
    h1 = net.get('h1')
    
    fetch_times = []
    
    # Executa 3 medições, esperando cada uma terminar
    for i in range(3):
        print(f"Fetching webpage attempt {i+1}/3...")
        # Comando curl para medir tempo total de transferência
        # -o /dev/null: descarta o output
        # -s: modo silencioso
        # -w %{time_total}: mostra apenas o tempo total
        curl_cmd = "curl -o /dev/null -s -w %%{time_total} http://%s/" % h1.IP()
        
        # Executa o comando e captura o output
        result = h2.popen(curl_cmd, shell=True, stdout=PIPE)
        output = result.communicate()[0].decode().strip()
        
        try:
            fetch_time = float(output)
            fetch_times.append(fetch_time)
            print(f"Fetch time: {fetch_time} seconds")
        except ValueError:
            print(f"Error parsing fetch time: {output}")
    
    return fetch_times

def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()

    # TODO: Start monitoring the queue sizes.  Since the switch I
    # created is "s0", I monitor one of the interfaces.  Which
    # interface?  The interface numbering starts with 1 and increases.
    # Depending on the order you add links to your network, this
    # number may be 1 or 2.  Ensure you use the correct number.
    
    # Monitorando a interface s0-eth2 (link do switch para h2 - o gargalo)
    # eth1 seria h1->switch, eth2 seria switch->h2
    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/q.txt' % (args.dir))

    # TODO: Start iperf, webservers, etc.
    # Iniciando o servidor web
    webserver_procs = start_webserver(net)
    
    # Iniciando iperf para criar fluxo TCP de longa duração
    iperf_server, iperf_client = start_iperf(net)
    
    # Iniciando ping para medir RTT
    ping_proc = start_ping(net)

    # TODO: measure the time it takes to complete webpage transfer
    # from h1 to h2 (say) 3 times.  Hint: check what the following
    # command does: curl -o /dev/null -s -w %{time_total} google.com
    # Now use the curl command to fetch webpage from the webserver you
    # spawned on host h1 (not from google!)
    # Hint: Verify the url by running your curl command without the
    # flags. The html webpage should be returned as the response.

    # Hint: have a separate function to do this and you may find the
    # loop below useful.
    
    all_fetch_times = []
    
    start_time = time()
    while True:
        # Mede o tempo de busca da página web 3 vezes a cada 5 segundos
        fetch_times = measure_webpage_fetch_time(net)
        all_fetch_times.extend(fetch_times)
        
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print("%.1fs left..." % (args.time - delta))

    # TODO: compute average (and standard deviation) of the fetch
    # times.  You don't need to plot them.  Just note it in your
    # README and explain.
    
    if all_fetch_times:
        import statistics
        avg_fetch_time = statistics.mean(all_fetch_times)
        std_fetch_time = statistics.stdev(all_fetch_times) if len(all_fetch_times) > 1 else 0
        
        print(f"\nWebpage fetch statistics:")
        print(f"Average fetch time: {avg_fetch_time:.4f} seconds")
        print(f"Standard deviation: {std_fetch_time:.4f} seconds")
        print(f"Number of samples: {len(all_fetch_times)}")
        
        # Salvando estatísticas em arquivo
        with open('%s/fetch_stats.txt' % args.dir, 'w') as f:
            f.write(f"Average fetch time: {avg_fetch_time:.4f} seconds\n")
            f.write(f"Standard deviation: {std_fetch_time:.4f} seconds\n")
            f.write(f"Number of samples: {len(all_fetch_times)}\n")
            f.write(f"All fetch times: {all_fetch_times}\n")

    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    # CLI(net)

    # Terminando todos os processos
    qmon.terminate()
    
    # Aguardando processos terminarem
    if 'iperf_server' in locals():
        iperf_server.terminate()
    if 'iperf_client' in locals():
        iperf_client.wait()
    if 'ping_proc' in locals():
        ping_proc.wait()
    
    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()