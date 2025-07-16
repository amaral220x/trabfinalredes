# Experimentos de Competição TCP: Reno vs BBR

## Visão Geral

Este projeto implementa experimentos para analisar a competição entre os algoritmos de controle de congestionamento TCP Reno e TCP BBR. O objetivo é determinar "quem sai ganhando" em diferentes cenários de rede.

## Arquivos Criados

### Scripts Principais

1. **`tcp_competition.py`** - Script principal que simula competição 1 vs 1 entre TCP Reno e TCP BBR
2. **`advanced_competition.py`** - Cenários avançados com múltiplos fluxos e configurações
3. **`analyze_competition.py`** - Análise detalhada dos resultados com gráficos
4. **`run_competition.sh`** - Script bash para executar experimentos facilmente

### Funcionalidades Implementadas

#### 1. Cenários de Competição

- **Cenário 1**: TCP Reno vs TCP BBR (1 vs 1)
- **Cenário 2**: Múltiplos TCP Reno vs Single TCP BBR
- **Cenário 3**: Fluxos com início em tempos diferentes
- **Cenário 4**: Variações de parâmetros de rede

#### 2. Métricas Coletadas

- **Throughput**: Largura de banda média, mínima, máxima e desvio padrão
- **RTT**: Tempo de ida e volta com análise de estabilidade
- **Fairness**: Índice de Jain para avaliar justiça entre fluxos
- **Utilização da Fila**: Análise de bufferbloat
- **Eficiência**: Utilização total da largura de banda

#### 3. Análise Visual

- Gráficos comparativos de throughput
- Distribuição de RTT (box plots)
- Evolução da fila ao longo do tempo
- Métricas de fairness e eficiência

## Como Usar

### Requisitos

```bash
# Instalar dependências
sudo apt-get install mininet python3-matplotlib python3-numpy
sudo apt-get install iperf
```

### Execução Básica

```bash
# Executar experimento simples
sudo ./run_competition.sh -b 10 -d 50 -q 100 -t 30

# Parâmetros:
# -b: Largura de banda do gargalo (Mbps)
# -d: Atraso de propagação (ms)
# -q: Tamanho da fila (pacotes)
# -t: Duração (segundos)
```

### Execução Avançada

```bash
# Executar todos os cenários
sudo python3 advanced_competition.py --all

# Executar cenário específico
sudo python3 advanced_competition.py --scenario 1
```

### Análise dos Resultados

```bash
# Analisar resultados existentes
python3 analyze_competition.py --dir results/nome_do_experimento --plot
```

## Interpretação dos Resultados

### 1. Throughput (Vazão)
- **Vencedor**: Algoritmo com maior throughput médio
- **Vantagem**: Percentual de superioridade
- **Estabilidade**: Menor desvio padrão indica maior estabilidade

### 2. Fairness (Justiça)
- **Índice de Jain**: 0 a 1 (1 = perfeitamente justo)
  - ≥ 0.9: Excelente fairness
  - ≥ 0.7: Boa fairness
  - ≥ 0.5: Fairness moderada
  - < 0.5: Fairness ruim

### 3. RTT (Latência)
- **RTT médio**: Tempo de resposta
- **Coeficiente de variação**: Estabilidade da latência
- **Bufferbloat**: RTT alto pode indicar bufferbloat

### 4. Utilização da Fila
- **< 50%**: Subutilização
- **50-80%**: Utilização adequada
- **> 80%**: Possível bufferbloat

## Cenários Interessantes Implementados

### Cenário 1: Competição Básica
- 1 fluxo TCP Reno vs 1 fluxo TCP BBR
- Mesmo tempo de início
- Análise de fairness básica

### Cenário 2: Múltiplos vs Single
- 2 fluxos TCP Reno vs 1 fluxo TCP BBR
- Analisa se BBR consegue competir contra múltiplos fluxos Reno
- Teste de agressividade

### Cenário 3: Entrada Temporal
- Fluxos começam em momentos diferentes
- Analisa como cada algoritmo reage a mudanças na rede
- Teste de adaptabilidade

### Cenário 4: Variações de Rede
- Diferentes larguras de banda
- Diferentes atrasos
- Diferentes tamanhos de fila

## Exemplos de Resultados Esperados

### Rede de Alta Largura de Banda, Baixo Atraso
- **Esperado**: TCP BBR pode ter vantagem devido à sua natureza proativa
- **Fairness**: Moderada (BBR pode ser mais agressivo)

### Rede de Baixa Largura de Banda, Alto Atraso
- **Esperado**: TCP BBR geralmente vence devido ao melhor controle de RTT
- **Bufferbloat**: TCP Reno pode causar mais bufferbloat

### Fila Pequena
- **Esperado**: Comportamento mais similar entre os algoritmos
- **Perdas**: Ambos podem ter perdas por fila cheia

## Arquivos de Saída

Para cada experimento, os seguintes arquivos são gerados:

```
results/experimento_TIMESTAMP/
├── competition_results.json     # Métricas detalhadas
├── competition_analysis.png     # Gráficos de análise
├── ping_reno.txt               # Dados de RTT TCP Reno
├── ping_bbr.txt                # Dados de RTT TCP BBR
├── queue.txt                   # Ocupação da fila
├── reno_flow_output.txt        # Saída iperf TCP Reno
├── bbr_flow_output.txt         # Saída iperf TCP BBR
└── README.md                   # Relatório do experimento
```

## Personalização

### Modificar Parâmetros de Rede
Edite as variáveis no início dos scripts:

```python
# Exemplo de configuração personalizada
--bw-net 20      # Largura de banda: 20 Mbps
--delay 100      # Atraso: 100 ms
--maxq 50        # Fila: 50 pacotes
--time 60        # Duração: 60 segundos
```

### Adicionar Novos Algoritmos
Para testar outros algoritmos TCP:

```python
# Adicionar CUBIC, por exemplo
set_tcp_algorithm(host, 'cubic')
```

### Modificar Topologia
Edite a classe `CompetitionTopo` para diferentes topologias de rede.

## Troubleshooting

### Erro "Mininet not found"
```bash
sudo apt-get install mininet
```

### Erro "Permission denied"
```bash
sudo chmod +x run_competition.sh
```

### Erro "iperf not found"
```bash
sudo apt-get install iperf
```

### Problemas com gráficos
```bash
sudo apt-get install python3-matplotlib python3-numpy
```

## Contribuições

Para adicionar novos cenários ou métricas:

1. Modifique `advanced_competition.py` para novos cenários
2. Atualize `analyze_competition.py` para novas métricas
3. Adicione documentação no README

## Referências

- [TCP BBR: Congestion-Based Congestion Control](https://queue.acm.org/detail.cfm?id=3022184)
- [TCP Reno: A New Approach to Congestion Control](https://tools.ietf.org/html/rfc2581)
- [Mininet Documentation](http://mininet.org/)
