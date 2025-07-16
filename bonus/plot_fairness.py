# plot_fairness.py
import re
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

def parse_iperf_data(filename):
    """Lê um arquivo de log do iperf e extrai a vazão (em Mbits/sec)."""
    throughputs = []
    regex = re.compile(r'(\d+\.\d+)\s+(Mbits/sec|Kbits/sec)')
    try:
        with open(filename, 'r') as f:
            for line in f:
                match = regex.search(line)
                if match and "0.0-" not in line:
                    value = float(match.group(1))
                    if match.group(2) == "Kbits/sec":
                        value /= 1000
                    throughputs.append(value)
    except FileNotFoundError:
        print(f"Erro: {filename} não encontrado.")
    return throughputs

def plot_graph(dir, total_bw):
    """Gera o gráfico de eficiência vs. fairness."""
    reno_data = parse_iperf_data(os.path.join(dir, 'iperf_reno.txt'))
    bbr_data = parse_iperf_data(os.path.join(dir, 'iperf_bbr.txt'))

    if not reno_data or not bbr_data:
        print("Não foi possível gerar o gráfico por falta de dados.")
        return

    min_len = min(len(reno_data), len(bbr_data))
    reno_thr, bbr_thr = np.array(reno_data[:min_len]), np.array(bbr_data[:min_len])

    plt.figure(figsize=(10, 10))
    plt.plot([0, total_bw], [total_bw, 0], 'k-', label=f'Eficiência (BW Total = {total_bw} Mbps)')
    plt.plot([0, total_bw], [0, total_bw], 'k--', label='Fairness')
    plt.plot(reno_thr, bbr_thr, 'r-o', label='Trajetória Reno vs. BBR', markersize=4, alpha=0.8)

    plt.title('Gráfico de Eficiência vs. Fairness (Reno vs. BBR)')
    plt.xlabel('Vazão TCP Reno (Mbits/s)'); plt.ylabel('Vazão TCP BBR (Mbits/s)')
    plt.grid(True); plt.legend()
    plt.xlim(0, total_bw * 1.1); plt.ylim(0, total_bw * 1.1)
    plt.gca().set_aspect('equal', adjustable='box')
    
    output_file = os.path.join(dir, 'fairness_vs_efficiency.png')
    print(f"Salvando o gráfico em {output_file}")
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 plot_fairness.py <diretorio_resultados> <banda_total_mbps>")
        sys.exit(1)
    plot_graph(sys.argv[1], float(sys.argv[2]))