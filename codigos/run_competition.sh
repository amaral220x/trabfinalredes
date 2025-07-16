#!/bin/bash

# Script para executar experimentos de competição TCP
# Autor: Análise de Redes - TCP Competition

echo "=== TCP Competition Experiment Runner ==="
echo "Este script executa experimentos de competição entre TCP Reno e TCP BBR"
echo

# Configurações padrão
DEFAULT_BANDWIDTH=10
DEFAULT_DELAY=10
DEFAULT_QUEUE=100
DEFAULT_TIME=30

# Função para mostrar uso
show_usage() {
    echo "Uso: $0 [opções]"
    echo "Opções:"
    echo "  -b, --bandwidth BANDWIDTH    Largura de banda do gargalo em Mbps (padrão: $DEFAULT_BANDWIDTH)"
    echo "  -d, --delay DELAY           Atraso de propagação em ms (padrão: $DEFAULT_DELAY)"
    echo "  -q, --queue QUEUE           Tamanho máximo da fila em pacotes (padrão: $DEFAULT_QUEUE)"
    echo "  -t, --time TIME             Duração do experimento em segundos (padrão: $DEFAULT_TIME)"
    echo "  -h, --help                  Mostra esta ajuda"
    echo
    echo "Exemplos:"
    echo "  $0 -b 10 -d 10 -q 100 -t 30"
    echo "  $0 --bandwidth 5 --delay 50 --queue 20"
}

# Análise dos parâmetros
BANDWIDTH=$DEFAULT_BANDWIDTH
DELAY=$DEFAULT_DELAY
QUEUE=$DEFAULT_QUEUE
TIME=$DEFAULT_TIME

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--bandwidth)
            BANDWIDTH="$2"
            shift 2
            ;;
        -d|--delay)
            DELAY="$2"
            shift 2
            ;;
        -q|--queue)
            QUEUE="$2"
            shift 2
            ;;
        -t|--time)
            TIME="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Criar diretório de resultados
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="results/competition_${TIMESTAMP}_bw${BANDWIDTH}_delay${DELAY}_q${QUEUE}"
mkdir -p $RESULTS_DIR

echo "Configuração do experimento:"
echo "  Largura de banda: ${BANDWIDTH} Mbps"
echo "  Atraso: ${DELAY} ms"
echo "  Tamanho da fila: ${QUEUE} pacotes"
echo "  Duração: ${TIME} segundos"
echo "  Diretório de resultados: ${RESULTS_DIR}"
echo

# Verificar dependências
check_dependencies() {
    echo "Verificando dependências..."
    
    if ! command -v python3 &> /dev/null; then
        echo "ERRO: Python3 não está instalado"
        exit 1
    fi
    
    if ! python3 -c "import mininet" &> /dev/null; then
        echo "ERRO: Mininet não está instalado"
        echo "Para instalar: sudo apt-get install mininet"
        exit 1
    fi
    
    if ! command -v iperf &> /dev/null; then
        echo "ERRO: iperf não está instalado"
        echo "Para instalar: sudo apt-get install iperf"
        exit 1
    fi
    
    echo "Dependências verificadas com sucesso!"
}

# Executar experimento
run_experiment() {
    echo "Iniciando experimento de competição TCP..."
    echo "Pressione Ctrl+C para interromper"
    echo
    
    # Executar o script principal
    sudo python3 tcp_competition.py \
        --bw-net $BANDWIDTH \
        --delay $DELAY \
        --maxq $QUEUE \
        --time $TIME \
        --dir $RESULTS_DIR
    
    if [ $? -eq 0 ]; then
        echo "Experimento concluído com sucesso!"
    else
        echo "Erro durante a execução do experimento"
        exit 1
    fi
}

# Analisar resultados
analyze_results() {
    echo "Analisando resultados..."
    
    if [ -f "$RESULTS_DIR/competition_results.json" ]; then
        python3 analyze_competition.py --dir $RESULTS_DIR --plot
        echo "Análise completa! Verifique o arquivo: $RESULTS_DIR/competition_analysis.png"
    else
        echo "Arquivo de resultados não encontrado. Executando apenas análise básica..."
        python3 analyze_competition.py --dir $RESULTS_DIR
    fi
}

# Gerar visualizações da competição
generate_competition_plots() {
    echo "Gerando visualizações da competição..."
    
    if [ -f "$RESULTS_DIR/competition_results.json" ]; then
        # Gerar dashboard interativo
        python3 plot_competition.py --dir $RESULTS_DIR --type dashboard
        
        # Gerar timeline da competição
        python3 plot_competition.py --dir $RESULTS_DIR --type timeline
        
        echo "Visualizações geradas:"
        echo "  - Dashboard: $RESULTS_DIR/competition_dashboard.png"
        echo "  - Timeline: $RESULTS_DIR/competition_timeline.png"
        echo "  - Animação: Execute 'python3 plot_competition.py --dir $RESULTS_DIR --type animated'"
    else
        echo "Arquivo de resultados não encontrado para visualizações"
    fi
}

# Executar diferentes cenários
run_scenarios() {
    echo "Executando múltiplos cenários..."
    
    # Cenário 1: Baixa largura de banda, baixo atraso
    echo "Cenário 1: Baixa largura de banda (5 Mbps), baixo atraso (10 ms)"
    SCENARIO_DIR="results/scenario1_low_bw_low_delay"
    mkdir -p $SCENARIO_DIR
    sudo python3 tcp_competition.py --bw-net 5 --delay 10 --maxq 100 --time 30 --dir $SCENARIO_DIR
    
    # Cenário 2: Baixa largura de banda, alto atraso
    echo "Cenário 2: Baixa largura de banda (5 Mbps), alto atraso (100 ms)"
    SCENARIO_DIR="results/scenario2_low_bw_high_delay"
    mkdir -p $SCENARIO_DIR
    sudo python3 tcp_competition.py --bw-net 5 --delay 100 --maxq 100 --time 30 --dir $SCENARIO_DIR
    
    # Cenário 3: Alta largura de banda, baixo atraso
    echo "Cenário 3: Alta largura de banda (50 Mbps), baixo atraso (10 ms)"
    SCENARIO_DIR="results/scenario3_high_bw_low_delay"
    mkdir -p $SCENARIO_DIR
    sudo python3 tcp_competition.py --bw-net 50 --delay 10 --maxq 100 --time 30 --dir $SCENARIO_DIR
    
    # Cenário 4: Fila pequena
    echo "Cenário 4: Fila pequena (20 pacotes)"
    SCENARIO_DIR="results/scenario4_small_queue"
    mkdir -p $SCENARIO_DIR
    sudo python3 tcp_competition.py --bw-net 10 --delay 50 --maxq 20 --time 30 --dir $SCENARIO_DIR
    
    echo "Todos os cenários executados!"
}

# Gerar relatório comparativo
generate_report() {
    echo "Gerando relatório comparativo..."
    
    cat > $RESULTS_DIR/README.md << EOF
# TCP Competition Experiment Results

## Configuração do Experimento
- **Largura de banda**: ${BANDWIDTH} Mbps
- **Atraso**: ${DELAY} ms
- **Tamanho da fila**: ${QUEUE} pacotes
- **Duração**: ${TIME} segundos
- **Data**: $(date)

## Arquivos Gerados
- \`competition_results.json\`: Métricas detalhadas do experimento
- \`competition_analysis.png\`: Gráficos de análise
- \`ping_reno.txt\`: Dados de RTT do TCP Reno
- \`ping_bbr.txt\`: Dados de RTT do TCP BBR
- \`queue.txt\`: Dados de ocupação da fila
- \`reno_flow_output.txt\`: Saída do iperf para TCP Reno
- \`bbr_flow_output.txt\`: Saída do iperf para TCP BBR

## Como Interpretar os Resultados

### Métricas de Throughput
- **Throughput médio**: Largura de banda média utilizada por cada algoritmo
- **Vantagem**: Percentual de vantagem do algoritmo vencedor

### Métricas de Fairness
- **Índice de Fairness**: Valor entre 0 e 1, onde 1 = perfeitamente justo
- **Interpretação**:
  - ≥ 0.9: Excelente fairness
  - ≥ 0.7: Boa fairness
  - ≥ 0.5: Fairness moderada
  - < 0.5: Fairness ruim

### Métricas de RTT
- **RTT médio**: Tempo de ida e volta médio
- **Estabilidade**: Menor coeficiente de variação indica maior estabilidade

### Métricas de Fila
- **Utilização da fila**: Percentual de ocupação da fila
- **Bufferbloat**: Utilização > 80% pode indicar bufferbloat
EOF

    echo "Relatório gerado em: $RESULTS_DIR/README.md"
}

# Menu interativo
show_menu() {
    echo "=== Menu de Experimentos TCP ==="
    echo "1. Executar experimento único"
    echo "2. Executar múltiplos cenários"
    echo "3. Apenas analisar resultados existentes"
    echo "4. Gerar visualizações da competição"
    echo "5. Visualização animada"
    echo "6. Mostrar configuração atual"
    echo "7. Sair"
    echo
    read -p "Escolha uma opção (1-7): " choice
    
    case $choice in
        1)
            check_dependencies
            run_experiment
            analyze_results
            generate_competition_plots
            generate_report
            ;;
        2)
            check_dependencies
            run_scenarios
            ;;
        3)
            read -p "Digite o diretório de resultados: " results_dir
            if [ -d "$results_dir" ]; then
                python3 analyze_competition.py --dir $results_dir --plot
            else
                echo "Diretório não encontrado: $results_dir"
            fi
            ;;
        4)
            read -p "Digite o diretório de resultados: " results_dir
            if [ -d "$results_dir" ]; then
                python3 plot_competition.py --dir $results_dir --type dashboard
                python3 plot_competition.py --dir $results_dir --type timeline
            else
                echo "Diretório não encontrado: $results_dir"
            fi
            ;;
        5)
            read -p "Digite o diretório de resultados: " results_dir
            if [ -d "$results_dir" ]; then
                python3 plot_competition.py --dir $results_dir --type animated
            else
                echo "Diretório não encontrado: $results_dir"
            fi
            ;;
        6)
            echo "Configuração atual:"
            echo "  Largura de banda: ${BANDWIDTH} Mbps"
            echo "  Atraso: ${DELAY} ms"
            echo "  Tamanho da fila: ${QUEUE} pacotes"
            echo "  Duração: ${TIME} segundos"
            ;;
        7)
            echo "Saindo..."
            exit 0
            ;;
        *)
            echo "Opção inválida!"
            show_menu
            ;;
    esac
}

# Função principal
main() {
    if [ $# -eq 0 ]; then
        show_menu
    else
        check_dependencies
        run_experiment
        analyze_results
        generate_competition_plots
        generate_report
    fi
}

# Executar função principal
main "$@"
