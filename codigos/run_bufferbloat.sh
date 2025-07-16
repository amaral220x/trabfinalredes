#!/bin/bash

# Script para executar comparação completa entre TCP Reno e TCP BBR
# Análise de Bufferbloat - Trabalho Final de Redes

echo "=========================================="
echo "    ANÁLISE DE BUFFERBLOAT: RENO vs BBR"
echo "=========================================="
echo

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para mostrar progresso
show_progress() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

show_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

show_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

show_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar dependências
check_dependencies() {
    show_progress "Verificando dependências..."
    
    local missing=0
    
    if ! command -v python3 &> /dev/null; then
        show_error "Python3 não encontrado"
        missing=1
    fi
    
    if ! command -v sudo &> /dev/null; then
        show_error "sudo não encontrado"
        missing=1
    fi
    
    if ! sudo python3 -c "import mininet" &> /dev/null; then
        show_error "Mininet não encontrado. Instale com: sudo apt-get install mininet"
        missing=1
    fi
    
    if ! command -v iperf &> /dev/null; then
        show_error "iperf não encontrado. Instale com: sudo apt-get install iperf"
        missing=1
    fi
    
    if ! python3 -c "import matplotlib" &> /dev/null; then
        show_error "matplotlib não encontrado. Instale com: sudo apt-get install python3-matplotlib"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        show_error "Dependências faltando. Por favor, instale-as antes de continuar."
        exit 1
    fi
    
    show_success "Todas as dependências estão instaladas"
}

# Limpar experimentos anteriores
cleanup_previous() {
    show_progress "Limpando experimentos anteriores..."
    
    sudo mn -c &> /dev/null
    sudo pkill -f "python.*bufferbloat.py" &> /dev/null
    sudo pkill -f "iperf" &> /dev/null
    sudo pkill -f "webserver.py" &> /dev/null
    
    show_success "Limpeza concluída"
}

# Executar experimentos TCP Reno
run_reno_experiments() {
    show_progress "Executando experimentos TCP Reno..."
    
    echo "📊 Cenário 1: TCP Reno com buffer grande (100 pacotes)"
    sudo python3 bufferbloat.py \
        --bw-net 1.5 \
        --delay 10 \
        --time 60 \
        --maxq 100 \
        --cong reno \
        --dir results/reno-q100
    
    if [ $? -eq 0 ]; then
        show_success "Experimento TCP Reno q=100 concluído"
    else
        show_error "Falha no experimento TCP Reno q=100"
        return 1
    fi
    
    echo "📊 Cenário 2: TCP Reno com buffer pequeno (20 pacotes)"
    sudo python3 bufferbloat.py \
        --bw-net 1.5 \
        --delay 10 \
        --time 60 \
        --maxq 20 \
        --cong reno \
        --dir results/reno-q20
    
    if [ $? -eq 0 ]; then
        show_success "Experimento TCP Reno q=20 concluído"
    else
        show_error "Falha no experimento TCP Reno q=20"
        return 1
    fi
    
    show_success "Todos os experimentos TCP Reno concluídos"
}

# Executar experimentos TCP BBR
run_bbr_experiments() {
    show_progress "Executando experimentos TCP BBR..."
    
    echo "📊 Cenário 3: TCP BBR com buffer grande (100 pacotes)"
    sudo python3 bufferbloat.py \
        --bw-net 1.5 \
        --delay 10 \
        --time 60 \
        --maxq 100 \
        --cong bbr \
        --dir results/bbr-q100
    
    if [ $? -eq 0 ]; then
        show_success "Experimento TCP BBR q=100 concluído"
    else
        show_error "Falha no experimento TCP BBR q=100"
        return 1
    fi
    
    echo "📊 Cenário 4: TCP BBR com buffer pequeno (20 pacotes)"
    sudo python3 bufferbloat.py \
        --bw-net 1.5 \
        --delay 10 \
        --time 60 \
        --maxq 20 \
        --cong bbr \
        --dir results/bbr-q20
    
    if [ $? -eq 0 ]; then
        show_success "Experimento TCP BBR q=20 concluído"
    else
        show_error "Falha no experimento TCP BBR q=20"
        return 1
    fi
    
    show_success "Todos os experimentos TCP BBR concluídos"
}

# Gerar todos os gráficos
generate_plots() {
    show_progress "Gerando gráficos..."
    
    # Criar diretório para imagens se não existir
    mkdir -p imagens
    
    # Gráficos individuais
    echo "📈 Gerando gráficos de ocupação da fila..."
    python3 plot_queue.py -f results/reno-q100/q.txt -o imagens/reno-buffer-q100.png
    python3 plot_queue.py -f results/reno-q20/q.txt -o imagens/reno-buffer-q20.png
    python3 plot_queue.py -f results/bbr-q100/q.txt -o imagens/bbr-buffer-q100.png
    python3 plot_queue.py -f results/bbr-q20/q.txt -o imagens/bbr-buffer-q20.png
    
    echo "📈 Gerando gráficos de RTT..."
    python3 plot_ping.py -f results/reno-q100/ping.txt -o imagens/reno-rtt-q100.png
    python3 plot_ping.py -f results/reno-q20/ping.txt -o imagens/reno-rtt-q20.png
    python3 plot_ping.py -f results/bbr-q100/ping.txt -o imagens/bbr-rtt-q100.png
    python3 plot_ping.py -f results/bbr-q20/ping.txt -o imagens/bbr-rtt-q20.png
    
    # Gráficos comparativos
    echo "📈 Gerando gráficos comparativos..."
    python3 plot_queue.py \
        -f results/reno-q100/q.txt results/bbr-q100/q.txt \
        -l "TCP Reno" "TCP BBR" \
        -o imagens/comparison-queue-q100.png
    
    python3 plot_queue.py \
        -f results/reno-q20/q.txt results/bbr-q20/q.txt \
        -l "TCP Reno" "TCP BBR" \
        -o imagens/comparison-queue-q20.png
    
    show_success "Gráficos gerados em: imagens/"
}

# Analisar resultados
analyze_results() {
    show_progress "Analisando resultados..."
    
    # Função para calcular estatísticas básicas de RTT
    analyze_rtt() {
        local file=$1
        local name=$2
        
        if [ -f "$file" ]; then
            local avg_rtt=$(grep "time=" "$file" | sed 's/.*time=\([0-9.]*\).*/\1/' | awk '{sum+=$1; n++} END {if(n>0) print sum/n; else print "N/A"}')
            local min_rtt=$(grep "time=" "$file" | sed 's/.*time=\([0-9.]*\).*/\1/' | sort -n | head -1)
            local max_rtt=$(grep "time=" "$file" | sed 's/.*time=\([0-9.]*\).*/\1/' | sort -n | tail -1)
            
            echo "  $name:"
            echo "    RTT médio: ${avg_rtt} ms"
            echo "    RTT mínimo: ${min_rtt} ms"
            echo "    RTT máximo: ${max_rtt} ms"
        else
            echo "  $name: Dados não encontrados"
        fi
    }
    
    # Função para analisar fetch stats
    analyze_fetch() {
        local file=$1
        local name=$2
        
        if [ -f "$file" ]; then
            echo "  $name:"
            grep "Average fetch time:" "$file" | sed 's/Average fetch time: /    Tempo médio de fetch: /'
            grep "Standard deviation:" "$file" | sed 's/Standard deviation: /    Desvio padrão: /'
            grep "Number of samples:" "$file" | sed 's/Number of samples: /    Número de amostras: /'
        else
            echo "  $name: Dados não encontrados"
        fi
    }
    
    echo
    echo "📊 ANÁLISE DE RESULTADOS"
    echo "========================"
    echo
    
    echo "🔍 Análise de RTT:"
    analyze_rtt "results/reno-q100/ping.txt" "TCP Reno (q=100)"
    analyze_rtt "results/reno-q20/ping.txt" "TCP Reno (q=20)"
    analyze_rtt "results/bbr-q100/ping.txt" "TCP BBR (q=100)"
    analyze_rtt "results/bbr-q20/ping.txt" "TCP BBR (q=20)"
    
    echo
    echo "🌐 Análise de Fetch Time:"
    analyze_fetch "results/reno-q100/fetch_stats.txt" "TCP Reno (q=100)"
    analyze_fetch "results/reno-q20/fetch_stats.txt" "TCP Reno (q=20)"
    analyze_fetch "results/bbr-q100/fetch_stats.txt" "TCP BBR (q=100)"
    analyze_fetch "results/bbr-q20/fetch_stats.txt" "TCP BBR (q=20)"
    
    echo
    echo "📈 Arquivos de gráficos gerados:"
    ls -la imagens/*.png 2>/dev/null || echo "Nenhum gráfico encontrado"
    
    echo
    echo "📁 Dados brutos disponíveis em:"
    echo "  results/reno-q100/    - TCP Reno com buffer grande"
    echo "  results/reno-q20/     - TCP Reno com buffer pequeno"
    echo "  results/bbr-q100/     - TCP BBR com buffer grande"
    echo "  results/bbr-q20/      - TCP BBR com buffer pequeno"
}

# Gerar relatório HTML
generate_html_report() {
    show_progress "Gerando relatório HTML..."
    
    cat > results/bufferbloat_report.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Relatório de Bufferbloat: TCP Reno vs TCP BBR</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
        .experiment { background-color: #f9f9f9; margin: 10px 0; padding: 15px; }
        .comparison { background-color: #e8f5e8; margin: 10px 0; padding: 15px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #fff; border: 1px solid #ccc; }
        img { max-width: 100%; height: auto; margin: 10px 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Análise de Bufferbloat</h1>
        <h2>TCP Reno vs TCP BBR</h2>
        <p>Comparação de algoritmos de controle de congestionamento</p>
    </div>
    
    <div class="section">
        <h3>Resumo dos Experimentos</h3>
        <p>Este relatório apresenta a análise comparativa entre TCP Reno e TCP BBR em cenários de bufferbloat.</p>
        <ul>
            <li>Largura de banda do gargalo: 1.5 Mbps</li>
            <li>Atraso de propagação: 10 ms (RTT base: 20 ms)</li>
            <li>Duração: 60 segundos por experimento</li>
            <li>Cenários: Buffer grande (100 pacotes) e pequeno (20 pacotes)</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>Gráficos de Ocupação da Fila</h3>
        <div class="grid">
            <div class="experiment">
                <h4>TCP Reno - Buffer Grande</h4>
                <img src="../imagens/reno-buffer-q100.png" alt="TCP Reno Buffer 100">
            </div>
            <div class="experiment">
                <h4>TCP BBR - Buffer Grande</h4>
                <img src="../imagens/bbr-buffer-q100.png" alt="TCP BBR Buffer 100">
            </div>
            <div class="experiment">
                <h4>TCP Reno - Buffer Pequeno</h4>
                <img src="../imagens/reno-buffer-q20.png" alt="TCP Reno Buffer 20">
            </div>
            <div class="experiment">
                <h4>TCP BBR - Buffer Pequeno</h4>
                <img src="../imagens/bbr-buffer-q20.png" alt="TCP BBR Buffer 20">
            </div>
        </div>
    </div>
    
    <div class="section">
        <h3>Gráficos de RTT</h3>
        <div class="grid">
            <div class="experiment">
                <h4>TCP Reno - RTT (q=100)</h4>
                <img src="../imagens/reno-rtt-q100.png" alt="TCP Reno RTT 100">
            </div>
            <div class="experiment">
                <h4>TCP BBR - RTT (q=100)</h4>
                <img src="../imagens/bbr-rtt-q100.png" alt="TCP BBR RTT 100">
            </div>
            <div class="experiment">
                <h4>TCP Reno - RTT (q=20)</h4>
                <img src="../imagens/reno-rtt-q20.png" alt="TCP Reno RTT 20">
            </div>
            <div class="experiment">
                <h4>TCP BBR - RTT (q=20)</h4>
                <img src="../imagens/bbr-rtt-q20.png" alt="TCP BBR RTT 20">
            </div>
        </div>
    </div>
    
    <div class="section">
        <h3>Comparações Diretas</h3>
        <div class="comparison">
            <h4>Buffer Grande (100 pacotes)</h4>
            <img src="../imagens/comparison-queue-q100.png" alt="Comparação Buffer 100">
        </div>
        <div class="comparison">
            <h4>Buffer Pequeno (20 pacotes)</h4>
            <img src="../imagens/comparison-queue-q20.png" alt="Comparação Buffer 20">
        </div>
    </div>
    
    <div class="section">
        <h3>Conclusões</h3>
        <ul>
            <li><strong>TCP BBR</strong> demonstra melhor controle de bufferbloat em buffers grandes</li>
            <li><strong>TCP Reno</strong> tende a encher completamente os buffers disponíveis</li>
            <li>Buffers pequenos reduzem bufferbloat mas podem causar perdas</li>
            <li>BBR mantém RTT mais estável independente do tamanho do buffer</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>Dados Brutos</h3>
        <p>Os dados brutos dos experimentos estão disponíveis em:</p>
        <ul>
            <li>results/reno-q100/ - TCP Reno com buffer grande</li>
            <li>results/reno-q20/ - TCP Reno com buffer pequeno</li>
            <li>results/bbr-q100/ - TCP BBR com buffer grande</li>
            <li>results/bbr-q20/ - TCP BBR com buffer pequeno</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    show_success "Relatório HTML gerado em: results/bufferbloat_report.html"
}

# Menu principal
show_menu() {
    echo "Escolha uma opção:"
    echo "1. Executar todos os experimentos"
    echo "2. Executar apenas TCP Reno"
    echo "3. Executar apenas TCP BBR"
    echo "4. Gerar apenas gráficos"
    echo "5. Analisar resultados existentes"
    echo "6. Gerar relatório HTML"
    echo "7. Limpar resultados"
    echo "8. Sair"
    echo
    read -p "Opção: " choice
    
    case $choice in
        1)
            check_dependencies
            cleanup_previous
            run_reno_experiments
            run_bbr_experiments
            generate_plots
            analyze_results
            generate_html_report
            ;;
        2)
            check_dependencies
            cleanup_previous
            run_reno_experiments
            ;;
        3)
            check_dependencies
            cleanup_previous
            run_bbr_experiments
            ;;
        4)
            generate_plots
            ;;
        5)
            analyze_results
            ;;
        6)
            generate_html_report
            ;;
        7)
            rm -rf results/ imagens/
            show_success "Resultados limpos"
            ;;
        8)
            echo "Saindo..."
            exit 0
            ;;
        *)
            show_error "Opção inválida"
            show_menu
            ;;
    esac
}

# Função principal
main() {
    if [ $# -eq 0 ]; then
        show_menu
    else
        case $1 in
            --all)
                check_dependencies
                cleanup_previous
                run_reno_experiments
                run_bbr_experiments
                generate_plots
                analyze_results
                generate_html_report
                ;;
            --reno)
                check_dependencies
                cleanup_previous
                run_reno_experiments
                ;;
            --bbr)
                check_dependencies
                cleanup_previous
                run_bbr_experiments
                ;;
            --plots)
                generate_plots
                ;;
            --analyze)
                analyze_results
                ;;
            --help)
                echo "Uso: $0 [--all|--reno|--bbr|--plots|--analyze|--help]"
                echo "  --all: Executa todos os experimentos"
                echo "  --reno: Executa apenas TCP Reno"
                echo "  --bbr: Executa apenas TCP BBR"
                echo "  --plots: Gera apenas gráficos"
                echo "  --analyze: Analisa resultados existentes"
                echo "  --help: Mostra esta ajuda"
                ;;
            *)
                show_error "Opção inválida: $1"
                exit 1
                ;;
        esac
    fi
}

# Executar função principal
main "$@"
