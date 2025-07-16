#!/bin/bash
# run_bonus.sh

sudo mn -c

# Parâmetros
DIR="bonus_results"
BW_NET=10
DELAY=20
TIME=20
MAX_Q=100

mkdir -p $DIR
echo "Diretório de resultados: $DIR"

# 1. Executa a simulação com a flag --bonus
echo "Iniciando simulação com --bonus..."
sudo python3 bufferbloat.py --bonus --bw-net $BW_NET --delay $DELAY --dir $DIR --time $TIME --maxq $MAX_Q

# 2. Gera o gráfico de fairness
echo "Gerando o gráfico de fairness..."
python3 plot_fairness.py $DIR $BW_NET

echo "-------------------------------------------------"
echo "Experimento Bônus concluído!"
echo "O gráfico foi salvo em: $DIR/fairness_vs_efficiency.png"
echo "Verifique também os arquivos iperf_*.txt em $DIR"
echo "-------------------------------------------------"