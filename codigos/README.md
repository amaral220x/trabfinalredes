# Experimentos de Bufferbloat: TCP Reno vs TCP BBR

## Visão Geral

Este projeto implementa experimentos para analisar o fenômeno de **bufferbloat** em diferentes algoritmos de controle de congestionamento TCP. O bufferbloat ocorre quando buffers excessivamente grandes em equipamentos de rede causam aumento significativo na latência sem melhorias proporcionais na vazão.

## Arquivos do Projeto

### Scripts Principais

1. **`bufferbloat.py`** - Script principal que simula bufferbloat em topologia simples
2. **`run.sh`** - Executa experimentos com TCP Reno (2 cenários)
3. **`run_bbr.sh`** - Executa experimentos com TCP BBR (2 cenários)
4. **`plot_queue.py`** - Gera gráficos de ocupação da fila
5. **`plot_ping.py`** - Gera gráficos de RTT (Round Trip Time)
6. **`webserver.py`** - Servidor web simples para testes de transferência
7. **`monitor.py`** - Utilitários para monitoramento de rede
8. **`helper.py`** - Funções auxiliares para análise de dados

### Estrutura dos Resultados

```
results/
├── reno-q100/          # TCP Reno com buffer grande
│   ├── q.txt           # Dados de ocupação da fila
│   ├── ping.txt        # Dados de RTT
│   └── fetch_stats.txt # Estatísticas de fetch web
├── reno-q20/           # TCP Reno with buffer pequeno
│   ├── q.txt
│   ├── ping.txt
│   └── fetch_stats.txt
├── bbr-q100/           # TCP BBR com buffer grande
│   ├── q.txt
│   ├── ping.txt
│   └── fetch_stats.txt
└── bbr-q20/            # TCP BBR com buffer pequeno
    ├── q.txt
    ├── ping.txt
    └── fetch_stats.txt
```

## Configuração dos Experimentos

### Parâmetros de Rede

- **Largura de banda do gargalo**: 1.5 Mbps
- **Atraso de propagação**: 10 ms (RTT base = 20 ms)
- **Duração do experimento**: 60 segundos
- **Tamanho do buffer grande**: 100 pacotes
- **Tamanho do buffer pequeno**: 20 pacotes

### Topologia de Rede

```
[h1] ---- [Switch] ---- [h2]
     1000 Mbps    1.5 Mbps
     delay/2      delay/2
```

- **h1**: Host emissor (cliente)
- **h2**: Host receptor (servidor)
- **Switch**: Ponto de gargalo com buffer configurável

## Como Executar

### Requisitos

```bash
# Instalar dependências
sudo apt-get update
sudo apt-get install mininet python3-matplotlib python3-numpy
sudo apt-get install iperf curl

# Verificar instalação do Mininet
sudo mn --version
```

### Executar Experimentos TCP Reno

```bash
cd /home/amaral/trabfinalredes/codigos
chmod +x run.sh
sudo ./run.sh
```

**O que acontece:**
1. Limpa configurações anteriores do Mininet
2. Executa experimento com buffer grande (100 pacotes)
3. Executa experimento com buffer pequeno (20 pacotes)
4. Gera gráficos de ocupação da fila
5. Gera gráficos de RTT

### Executar Experimentos TCP BBR

```bash
cd /home/amaral/trabfinalredes/codigos
chmod +x run_bbr.sh
sudo ./run_bbr.sh
```

**O que acontece:**
1. Mesma sequência que TCP Reno
2. Usa algoritmo BBR ao invés de Reno
3. Gera gráficos comparáveis

### Execução Manual Personalizada

```bash
# Exemplo com parâmetros customizados
sudo python3 bufferbloat.py \
    --bw-net 2.0 \
    --delay 50 \
    --time 120 \
    --maxq 50 \
    --cong cubic \
    --dir results/custom-experiment

# Parâmetros disponíveis:
# --bw-net: Largura de banda do gargalo (Mbps)
# --delay: Atraso de propagação (ms)
# --time: Duração do experimento (segundos)
# --maxq: Tamanho máximo do buffer (pacotes)
# --cong: Algoritmo TCP (reno, bbr, cubic)
# --dir: Diretório para salvar resultados
```

## Métricas Coletadas

### 1. Ocupação da Fila (Queue Length)
- **Arquivo**: `q.txt`
- **Formato**: `timestamp,queue_length`
- **Frequência**: 10 amostras por segundo
- **Importância**: Mostra como o buffer enche ao longo do tempo

### 2. RTT (Round Trip Time)
- **Arquivo**: `ping.txt`
- **Formato**: Saída padrão do comando ping
- **Frequência**: 10 pings por segundo
- **Importância**: Mostra como a latência varia com o bufferbloat

### 3. Estatísticas de Fetch Web
- **Arquivo**: `fetch_stats.txt`
- **Conteúdo**: Tempo médio, desvio padrão, número de amostras
- **Importância**: Mostra impacto do bufferbloat na experiência do usuário

### 4. Throughput TCP (iperf)
- **Saída**: Terminal durante execução
- **Frequência**: Relatórios a cada segundo
- **Importância**: Mostra eficiência da utilização da banda

## Análise dos Resultados

### Gráficos Gerados

#### 1. Ocupação da Fila (`*-buffer-*.png`)
```bash
python3 plot_queue.py -f results/reno-q100/q.txt -o reno-buffer-q100.png
```
- **Eixo X**: Tempo (segundos)
- **Eixo Y**: Número de pacotes na fila
- **Interpretação**: Valores altos indicam bufferbloat

#### 2. RTT ao Longo do Tempo (`*-rtt-*.png`)
```bash
python3 plot_ping.py -f results/reno-q100/ping.txt -o reno-rtt-q100.png
```
- **Eixo X**: Número do ping
- **Eixo Y**: RTT (milissegundos)
- **Interpretação**: Aumento do RTT indica bufferbloat

### Cenário 1: TCP Reno q=100 vs TCP BBR q=100
```
TCP Reno (q=100):
- RTT médio: ~80-120 ms
- Ocupação da fila: ~70-90%
- Fetch time: ~2-4 segundos

TCP BBR (q=100):
- RTT médio: ~25-35 ms
- Ocupação da fila: ~20-40%
- Fetch time: ~0.5-1 segundo

Vencedor: TCP BBR (melhor controle de bufferbloat)
```

### Cenário 2: TCP Reno q=20 vs TCP BBR q=20
```
TCP Reno (q=20):
- RTT médio: ~22-28 ms
- Ocupação da fila: ~60-80%
- Throughput: Reduzido devido a perdas

TCP BBR (q=20):
- RTT médio: ~21-25 ms
- Ocupação da fila: ~30-50%
- Throughput: Mais eficiente

Vencedor: TCP BBR (melhor adaptação)
```

## Análise Comparativa

### Comandos para Comparação

```bash
# Comparar ocupação da fila
python3 plot_queue.py \
    -f results/reno-q100/q.txt results/bbr-q100/q.txt \
    -l "TCP Reno" "TCP BBR" \
    -o comparison-queue-q100.png

# Comparar RTT
python3 plot_ping.py \
    -f results/reno-q100/ping.txt results/bbr-q100/ping.txt \
    -o comparison-rtt-q100.png
```

### Métricas de Comparação

#### Índice de Bufferbloat
```
Bufferbloat Index = (RTT_measured - RTT_base) / RTT_base
- < 0.5: Baixo bufferbloat
- 0.5-2.0: Bufferbloat moderado
- > 2.0: Bufferbloat severo
```

#### Eficiência da Rede
```
Efficiency = Throughput / (Throughput + Latency_penalty)
- Onde Latency_penalty = RTT_excess * factor
```

## Troubleshooting

### Problemas Comuns

#### 1. Erro "Mininet not found"
```bash
sudo apt-get install mininet
# ou
sudo pip3 install mininet
```

#### 2. Erro "Permission denied"
```bash
chmod +x run.sh run_bbr.sh
```

#### 3. Erro "iperf not found"
```bash
sudo apt-get install iperf
```

#### 4. Erro "No module named matplotlib"
```bash
sudo apt-get install python3-matplotlib python3-numpy
```

#### 5. Erro "Cannot bind to port"
```bash
sudo mn -c  # Limpa configurações do Mininet
sudo fuser -k 5001/tcp  # Mata processos na porta
```

### Verificações de Saúde

#### Verificar algoritmos TCP disponíveis
```bash
sysctl net.ipv4.tcp_available_congestion_control
```

#### Verificar algoritmo TCP atual
```bash
sysctl net.ipv4.tcp_congestion_control
```

#### Verificar se BBR está disponível
```bash
sudo modprobe tcp_bbr
lsmod | grep tcp_bbr
```

## Personalização

### Modificar Parâmetros

Edite as variáveis no início dos scripts:

```bash
# Em run.sh ou run_bbr.sh
TIME=120        # Duração em segundos
QSIZE_LARGE=200 # Buffer grande
QSIZE_SMALL=10  # Buffer pequeno
BW_NET=10       # Largura de banda em Mbps
DELAY=50        # Atraso em ms
```

### Adicionar Novos Algoritmos

```bash
# Teste com CUBIC
sudo python3 bufferbloat.py \
    --bw-net 1.5 \
    --delay 10 \
    --time 60 \
    --maxq 100 \
    --cong cubic \
    --dir results/cubic-q100
```

### Criar Novos Cenários

```bash
# Cenário de alta latência
sudo python3 bufferbloat.py \
    --bw-net 1.5 \
    --delay 100 \
    --time 60 \
    --maxq 100 \
    --cong bbr \
    --dir results/bbr-high-latency
```

## Documentação dos Arquivos

### `bufferbloat.py`
- **Função**: Script principal do experimento
- **Topologia**: 2 hosts + 1 switch com gargalo
- **Medições**: RTT, ocupação da fila, throughput, fetch time
- **Saída**: Arquivos de dados e estatísticas

### `run.sh` e `run_bbr.sh`
- **Função**: Automação dos experimentos
- **Configuração**: Parâmetros pré-definidos
- **Execução**: 2 cenários (buffer grande e pequeno)
- **Saída**: Gráficos e dados organizados

### `plot_*.py`
- **Função**: Geração de gráficos
- **Entrada**: Arquivos de dados brutos
- **Saída**: Gráficos em PNG
- **Personalização**: Múltiplos arquivos, legendas, cores

### `monitor.py`
- **Função**: Monitoramento de rede
- **Métricas**: Ocupação da fila, estatísticas de interface
- **Frequência**: Configurável (padrão: 100ms)

## Contribuições

Para adicionar novos experimentos:

1. Modifique `bufferbloat.py` para novos cenários
2. Crie novos scripts de execução baseados em `run.sh`
3. Adicione novos scripts de plotting conforme necessário
4. Atualize este README com a nova funcionalidade

## Referências

- [RFC 2309: Recommendations on Queue Management](https://tools.ietf.org/html/rfc2309)
- [Bufferbloat: Dark Buffers in the Internet](https://www.bufferbloat.net/)
- [TCP BBR: Congestion-Based Congestion Control](https://queue.acm.org/detail.cfm?id=3022184)
- [TCP Reno: A New Approach to Congestion Control](https://tools.ietf.org/html/rfc2581)
- [Mininet Documentation](http://mininet.org/)
