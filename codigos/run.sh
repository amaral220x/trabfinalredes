#!/bin/bash

# Script para executar experimentos de bufferbloat com TCP Reno

# Limpar qualquer configuração anterior do Mininet
sudo mn -c

# Configurações do experimento
TIME=60  # Duração do experimento em segundos
QSIZE_LARGE=100  # Tamanho grande do buffer
QSIZE_SMALL=20   # Tamanho pequeno do buffer
BW_NET=1.5       # Largura de banda do link gargalo (Mb/s)
DELAY=10         # Delay de propagação (ms) - RTT total será 20ms

# Criar diretório para resultados se não existir
mkdir -p results

echo "Executando experimento com TCP Reno..."

# Experimento 1: Buffer grande (q=100)
echo "Experimento 1: Buffer grande (q=100 pacotes)"
sudo python3 bufferbloat.py \
    --bw-net $BW_NET \
    --delay $DELAY \
    --time $TIME \
    --maxq $QSIZE_LARGE \
    --cong reno \
    --dir results/reno-q100

# Experimento 2: Buffer pequeno (q=20)
echo "Experimento 2: Buffer pequeno (q=20 pacotes)"
sudo python3 bufferbloat.py \
    --bw-net $BW_NET \
    --delay $DELAY \
    --time $TIME \
    --maxq $QSIZE_SMALL \
    --cong reno \
    --dir results/reno-q20

# Gerar gráficos
echo "Gerando gráficos..."

# Gráficos para buffer grande
python3 plot_queue.py -f results/reno-q100/q.txt -o reno-buffer-q100.png
python3 plot_ping.py -f results/reno-q100/ping.txt -o reno-rtt-q100.png

# Gráficos para buffer pequeno
python3 plot_queue.py -f results/reno-q20/q.txt -o reno-buffer-q20.png
python3 plot_ping.py -f results/reno-q20/ping.txt -o reno-rtt-q20.png

echo "Experimentos TCP Reno concluídos!"
echo "Gráficos salvos como:"
echo "- reno-buffer-q100.png"
echo "- reno-rtt-q100.png"
echo "- reno-buffer-q20.png"
echo "- reno-rtt-q20.png"

echo ""
echo "Estatísticas de fetch das páginas web:"
echo "Buffer grande (q=100):"
cat results/reno-q100/fetch_stats.txt
echo ""
echo "Buffer pequeno (q=20):"
cat results/reno-q20/fetch_stats.txt