# Guia de Visualizações da Competição TCP

## Visão Geral

Este guia explica como usar as ferramentas de visualização para entender melhor a competição entre TCP Reno e TCP BBR.

## Tipos de Visualizações

### 1. 🎯 Dashboard Completo
**Arquivo**: `competition_dashboard.png`
**Comando**: `python3 plot_competition.py --dir results/experimento --type dashboard`

**O que mostra:**
- Comparação de throughput com destaque para o vencedor
- Timeline em tempo real da competição
- Gauge de fairness (justiça)
- Comparação de RTT (latência)
- Resumo textual dos resultados
- Ocupação da fila ao longo do tempo

### 2. 📈 Timeline da Competição
**Arquivo**: `competition_timeline.png`
**Comando**: `python3 plot_competition.py --dir results/experimento --type timeline`

**O que mostra:**
- **Gráfico Superior**: Throughput instantâneo de cada algoritmo
- **Gráfico Médio**: Dados cumulativos transferidos (quem está ganhando)
- **Gráfico Inferior**: Vantagem instantânea (barras vermelhas = BBR ganha, azuis = Reno ganha)

### 3. 🎬 Animação em Tempo Real
**Comando**: `python3 plot_competition.py --dir results/experimento --type animated`

**O que mostra:**
- Animação mostrando a evolução da competição
- Placar em tempo real
- Líder atual destacado
- Evolução das curvas de throughput

## Como Usar

### Método 1: Script Integrado
```bash
# Executar experimento com visualizações automáticas
sudo ./run_competition.sh

# No menu, escolher opção 1 (gera visualizações automaticamente)
# Ou opção 4 para gerar apenas visualizações de resultados existentes
```

### Método 2: Script Dedicado
```bash
# Gerar dashboard
./visualize_competition.sh results/competition_20231201_120000 dashboard

# Gerar timeline
./visualize_competition.sh results/competition_20231201_120000 timeline

# Gerar animação
./visualize_competition.sh results/competition_20231201_120000 animated

# Gerar todas as visualizações
./visualize_competition.sh results/competition_20231201_120000 all
```

### Método 3: Comando Direto
```bash
# Dashboard completo
python3 plot_competition.py --dir results/experimento --type dashboard

# Timeline da competição
python3 plot_competition.py --dir results/experimento --type timeline

# Animação interativa
python3 plot_competition.py --dir results/experimento --type animated
```

## Interpretação dos Gráficos

### Dashboard - Seção por Seção

#### 🏆 Throughput Battle (Superior Esquerdo)
- **Barras azuis**: TCP Reno
- **Barras vermelhas**: TCP BBR
- **Borda dourada**: Algoritmo vencedor
- **Valores**: Throughput médio em Mbps

#### ⚡ Real-time Competition (Superior Centro/Direito)
- **Linha azul**: Throughput TCP Reno ao longo do tempo
- **Linha vermelha**: Throughput TCP BBR ao longo do tempo
- **Interpretação**: Mostra flutuações e padrões de cada algoritmo

#### ⚖️ Fairness Index (Médio Esquerdo)
- **Ponteiro vermelho**: Índice de fairness atual
- **Valores**:
  - 0.9-1.0: Excelente fairness
  - 0.7-0.9: Boa fairness
  - 0.5-0.7: Fairness moderada
  - < 0.5: Fairness ruim

#### 📡 Latency Comparison (Médio Centro)
- **Box plots**: Distribuição de RTT
- **Caixa azul**: TCP Reno
- **Caixa vermelha**: TCP BBR
- **Interpretação**: Caixas menores = latência mais estável

#### 🏁 Competition Summary (Médio Direito)
- **Texto**: Resumo dos resultados
- **Vencedor**: Algoritmo com maior throughput
- **Vantagem**: Percentual de superioridade
- **Fairness**: Avaliação qualitativa

#### 📈 Queue Occupancy (Inferior)
- **Área verde**: Ocupação da fila ao longo do tempo
- **Valores altos**: Possível bufferbloat
- **Flutuações**: Padrões de comportamento dos algoritmos

### Timeline - Interpretação Detalhada

#### Throughput Over Time
- **Oscilações**: Naturais devido ao controle de congestionamento
- **Reno**: Padrão "sawtooth" típico
- **BBR**: Comportamento mais estável

#### Cumulative Data Transferred
- **Curva mais íngreme**: Algoritmo mais eficiente
- **Distância entre curvas**: Vantagem acumulada
- **Cruzamentos**: Mudanças na liderança

#### Instantaneous Advantage
- **Barras vermelhas**: BBR está ganhando naquele momento
- **Barras azuis**: Reno está ganhando naquele momento
- **Altura das barras**: Magnitude da vantagem

### Animação - Como Assistir

#### Elementos da Animação
- **Linhas crescentes**: Throughput em tempo real
- **Placar**: Totais acumulados
- **Cor do líder**: Azul (Reno) ou Vermelho (BBR)
- **Velocidade**: Configurável (padrão: 200ms por frame)

#### Padrões para Observar
- **Momentos de ultrapassagem**: Quando um algoritmo supera o outro
- **Estabilidade**: Qual algoritmo mantém throughput mais constante
- **Reação a eventos**: Como cada algoritmo responde a mudanças

## Cenários de Análise

### Cenário 1: BBR Dominante
**Sinais visuais:**
- Barras vermelhas predominantes no gráfico de vantagem
- Curva BBR acima da curva Reno no timeline
- Fairness index baixo (< 0.7)

**Interpretação:** BBR está sendo mais agressivo

### Cenário 2: Competição Equilibrada
**Sinais visuais:**
- Alternância entre barras vermelhas e azuis
- Curvas próximas no timeline
- Fairness index alto (> 0.8)

**Interpretação:** Algoritmos competindo de forma justa

### Cenário 3: Reno Dominante
**Sinais visuais:**
- Barras azuis predominantes
- Curva Reno acima da curva BBR
- Possível RTT alto (bufferbloat)

**Interpretação:** Reno pode estar causando bufferbloat

## Dicas de Uso

### Para Análise Rápida
1. **Use o dashboard** para visão geral
2. **Verifique o winner** na seção summary
3. **Observe o fairness index** para avaliar justiça

### Para Análise Detalhada
1. **Use o timeline** para ver evolução temporal
2. **Analise o gráfico de vantagem** para entender momentos críticos
3. **Use a animação** para ver a competição "ao vivo"

### Para Apresentações
1. **Dashboard**: Melhor para slides
2. **Timeline**: Bom para explicar evolução
3. **Animação**: Impressionante para demonstrações

## Personalização

### Modificar Cores
Edite o arquivo `plot_competition.py`:
```python
colors = ['#3498db', '#e74c3c']  # Azul e vermelho
```

### Alterar Tamanho das Figuras
```python
fig = plt.figure(figsize=(16, 12))  # Largura, altura
```

### Adicionar Métricas
Edite as funções de parsing para incluir novos dados do experimento.

## Troubleshooting

### Erro: "Dados não encontrados"
- Verifique se o experimento foi executado completamente
- Confirme que os arquivos de output existem no diretório

### Erro: "Matplotlib not found"
```bash
sudo apt-get install python3-matplotlib python3-numpy
```

### Erro: "Seaborn not found"
```bash
pip3 install seaborn
```

### Gráficos não aparecem
- Verifique se está rodando em ambiente gráfico
- Use `plt.savefig()` para salvar ao invés de `plt.show()`

## Exemplos Práticos

### Exemplo 1: Análise Básica
```bash
# Executar experimento
sudo ./run_competition.sh -b 10 -d 50 -q 100 -t 30

# Gerar dashboard
./visualize_competition.sh results/competition_* dashboard
```

### Exemplo 2: Comparação de Cenários
```bash
# Executar múltiplos cenários
sudo ./run_competition.sh -b 5 -d 10 -q 20 -t 30
sudo ./run_competition.sh -b 5 -d 100 -q 20 -t 30

# Comparar visualmente
./visualize_competition.sh results/competition_scenario1 all
./visualize_competition.sh results/competition_scenario2 all
```

### Exemplo 3: Análise de Fairness
```bash
# Executar experimento longo
sudo ./run_competition.sh -b 10 -d 50 -q 100 -t 120

# Focar na análise de fairness
./visualize_competition.sh results/competition_* dashboard
# Observe especialmente o fairness gauge
```

## Conclusão

As visualizações permitem entender facilmente:
- **Quem ganha** em diferentes cenários
- **Como** a competição evolui ao longo do tempo
- **Por que** um algoritmo supera o outro
- **Justiça** da competição entre algoritmos

Use as diferentes visualizações de acordo com sua necessidade de análise!
