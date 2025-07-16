#!/bin/bash

# Script para gerar visualizações da competição TCP
# Uso: ./visualize_competition.sh [diretório_resultados] [tipo]

echo "🎨 Gerador de Visualizações da Competição TCP"
echo "============================================="

# Verificar argumentos
if [ $# -eq 0 ]; then
    echo "Uso: $0 <diretório_resultados> [tipo]"
    echo "Tipos disponíveis:"
    echo "  - dashboard (padrão): Dashboard completo"
    echo "  - timeline: Timeline da competição"
    echo "  - animated: Animação em tempo real"
    echo "  - all: Todas as visualizações"
    echo
    echo "Exemplo: $0 results/competition_20231201_120000 dashboard"
    exit 1
fi

RESULTS_DIR=$1
VIS_TYPE=${2:-dashboard}

# Verificar se o diretório existe
if [ ! -d "$RESULTS_DIR" ]; then
    echo "❌ Erro: Diretório não encontrado: $RESULTS_DIR"
    exit 1
fi

# Verificar se existem resultados
if [ ! -f "$RESULTS_DIR/competition_results.json" ]; then
    echo "❌ Erro: Arquivo de resultados não encontrado: $RESULTS_DIR/competition_results.json"
    echo "Execute primeiro um experimento de competição!"
    exit 1
fi

echo "📁 Diretório de resultados: $RESULTS_DIR"
echo "📊 Tipo de visualização: $VIS_TYPE"
echo

# Função para gerar dashboard
generate_dashboard() {
    echo "🎯 Gerando dashboard completo..."
    python3 plot_competition.py --dir "$RESULTS_DIR" --type dashboard
    
    if [ $? -eq 0 ]; then
        echo "✅ Dashboard gerado: $RESULTS_DIR/competition_dashboard.png"
    else
        echo "❌ Erro ao gerar dashboard"
        return 1
    fi
}

# Função para gerar timeline
generate_timeline() {
    echo "📈 Gerando timeline da competição..."
    python3 plot_competition.py --dir "$RESULTS_DIR" --type timeline
    
    if [ $? -eq 0 ]; then
        echo "✅ Timeline gerado: $RESULTS_DIR/competition_timeline.png"
    else
        echo "❌ Erro ao gerar timeline"
        return 1
    fi
}

# Função para gerar animação
generate_animation() {
    echo "🎬 Gerando animação da competição..."
    echo "⚠️  Pressione Ctrl+C para sair da animação"
    python3 plot_competition.py --dir "$RESULTS_DIR" --type animated
    
    if [ $? -eq 0 ]; then
        echo "✅ Animação exibida com sucesso"
    else
        echo "❌ Erro ao gerar animação"
        return 1
    fi
}

# Executar baseado no tipo
case $VIS_TYPE in
    dashboard)
        generate_dashboard
        ;;
    timeline)
        generate_timeline
        ;;
    animated)
        generate_animation
        ;;
    all)
        echo "🎨 Gerando todas as visualizações..."
        generate_dashboard
        generate_timeline
        
        echo
        read -p "Deseja ver a animação? (y/n): " answer
        if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
            generate_animation
        fi
        ;;
    *)
        echo "❌ Tipo de visualização inválido: $VIS_TYPE"
        echo "Tipos disponíveis: dashboard, timeline, animated, all"
        exit 1
        ;;
esac

echo
echo "🎉 Visualizações concluídas!"
echo "📁 Arquivos gerados em: $RESULTS_DIR"

# Listar arquivos gerados
echo "📄 Arquivos disponíveis:"
ls -la "$RESULTS_DIR"/*.png 2>/dev/null || echo "Nenhum arquivo PNG encontrado"

# Mostrar resumo dos resultados
echo
echo "📊 RESUMO DOS RESULTADOS:"
echo "========================"

if [ -f "$RESULTS_DIR/competition_results.json" ]; then
    python3 -c "
import json
with open('$RESULTS_DIR/competition_results.json', 'r') as f:
    results = json.load(f)

if 'winner' in results:
    print(f'🏆 Vencedor: {results[\"winner\"]}')
    print(f'📊 Vantagem: {results.get(\"advantage\", 0):.1f}%')

if 'reno_flow' in results and 'bbr_flow' in results:
    print(f'🔵 TCP Reno: {results[\"reno_flow\"][\"avg_throughput\"]:.1f} Mbps')
    print(f'🔴 TCP BBR: {results[\"bbr_flow\"][\"avg_throughput\"]:.1f} Mbps')

if 'fairness_index' in results:
    fairness = results['fairness_index']
    fairness_desc = 'Excelente' if fairness >= 0.9 else 'Boa' if fairness >= 0.7 else 'Moderada' if fairness >= 0.5 else 'Ruim'
    print(f'⚖️ Fairness: {fairness:.3f} ({fairness_desc})')
"
else
    echo "Arquivo de resultados não encontrado"
fi

echo
echo "💡 Dicas:"
echo "  - Use 'dashboard' para visão geral completa"
echo "  - Use 'timeline' para ver evolução temporal"
echo "  - Use 'animated' para competição em tempo real"
echo "  - Use 'all' para gerar todas as visualizações"
