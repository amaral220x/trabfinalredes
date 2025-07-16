# Novos Cenários de Competição TCP

## Cenários Implementados

### 1. Cenário Original: 1 vs 1
- **Comando**: `reno_vs_bbr`
- **Descrição**: 1 fluxo TCP Reno vs 1 fluxo TCP BBR
- **Hosts**: h1 (Reno), h2 (BBR)
- **Uso**: Comparação direta entre os algoritmos

### 2. Novo Cenário: 2 vs 2
- **Comando**: `2reno_vs_2bbr`
- **Descrição**: 2 fluxos TCP Reno vs 2 fluxos TCP BBR
- **Hosts**: h1, h2 (Reno), h3, h4 (BBR)
- **Uso**: Avalia comportamento com múltiplos fluxos do mesmo algoritmo

### 3. Novo Cenário: 2 vs 1
- **Comando**: `2reno_vs_1bbr`
- **Descrição**: 2 fluxos TCP Reno vs 1 fluxo TCP BBR
- **Hosts**: h1, h2 (Reno), h3 (BBR)
- **Uso**: Avalia fairness quando há desbalanceamento de fluxos

## Como Executar

### Usando o script de automação:
```bash
cd /home/amaral/trabfinalredes/codigos
chmod +x run_competition.sh
./run_competition.sh
```

### Menu interativo:
1. **Experimento 1 vs 1**: Executa o cenário original
2. **Experimento 2 vs 2**: Executa 2 Reno vs 2 BBR
3. **Experimento 2 vs 1**: Executa 2 Reno vs 1 BBR
4. **Executar múltiplos cenários**: Executa todos os cenários automaticamente

### Execução direta:
```bash
# Cenário 1 vs 1
sudo python3 tcp_competition.py --scenario reno_vs_bbr --dir results/1v1

# Cenário 2 vs 2
sudo python3 tcp_competition.py --scenario 2reno_vs_2bbr --dir results/2v2

# Cenário 2 vs 1
sudo python3 tcp_competition.py --scenario 2reno_vs_1bbr --dir results/2v1
```

## Análise dos Resultados

### Métricas Calculadas:
- **Throughput agregado**: Soma dos throughputs de cada algoritmo
- **Fairness Index**: Índice de Jain para medir equidade
- **RTT médio**: Tempo de resposta médio
- **Utilização da fila**: Ocupação do buffer

### Interpretação:
- **Cenário 1 vs 1**: Comparação direta de eficiência
- **Cenário 2 vs 2**: Avalia escalabilidade e comportamento agregado
- **Cenário 2 vs 1**: Testa fairness em situações desbalanceadas

## Arquivos Modificados

1. **tcp_competition.py**:
   - Classe `CompetitionTopo` estendida com métodos `build_2v2()` e `build_2v1()`
   - Função `run_competition_experiment()` atualizada para suportar múltiplos cenários

2. **analyze_competition.py**:
   - Função `analyze_competition_results()` adaptada para múltiplos fluxos
   - Cálculo de métricas agregadas

3. **run_competition.sh**:
   - Menu atualizado com opções para cada cenário
   - Função `run_scenarios()` com todos os cenários

## Próximos Passos

Para testar os novos cenários:

1. **Executar um cenário específico**:
   ```bash
   ./run_competition.sh
   # Escolher opção 2 ou 3
   ```

2. **Executar todos os cenários**:
   ```bash
   ./run_competition.sh
   # Escolher opção 4
   ```

3. **Analisar resultados**:
   - Os resultados ficam salvos em `results/scenarioX_*/`
   - Gráficos são gerados automaticamente
   - Métricas são calculadas e salvas em JSON

## Exemplo de Uso

```bash
# Executar o cenário 2 vs 2
sudo python3 tcp_competition.py \
  --bw-net 10 \
  --delay 50 \
  --maxq 100 \
  --time 30 \
  --scenario 2reno_vs_2bbr \
  --dir results/test_2v2

# Analisar resultados
python3 analyze_competition.py --dir results/test_2v2 --plot

# Gerar visualizações
python3 plot_competition.py --dir results/test_2v2 --type dashboard
```

Os novos cenários estão prontos para uso e permitem uma análise mais abrangente da competição entre TCP Reno e TCP BBR!
