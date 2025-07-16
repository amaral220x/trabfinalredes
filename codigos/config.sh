# Configuração dos Experimentos de Bufferbloat
# =============================================

# Parâmetros de Rede
NETWORK_BANDWIDTH=1.5      # Largura de banda do gargalo (Mbps)
NETWORK_DELAY=10           # Atraso de propagação (ms)
HOST_BANDWIDTH=1000        # Largura de banda dos hosts (Mbps)

# Parâmetros dos Experimentos
EXPERIMENT_DURATION=60     # Duração de cada experimento (segundos)
BUFFER_SIZE_LARGE=100      # Tamanho do buffer grande (pacotes)
BUFFER_SIZE_SMALL=20       # Tamanho do buffer pequeno (pacotes)

# Algoritmos TCP para testar
TCP_ALGORITHMS=("reno" "bbr" "cubic")

# Parâmetros de Monitoramento
PING_INTERVAL=0.1          # Intervalo entre pings (segundos)
QUEUE_MONITOR_INTERVAL=0.1 # Intervalo de monitoramento da fila (segundos)
FETCH_ATTEMPTS=3           # Número de tentativas de fetch web

# Diretórios
RESULTS_DIR="results"      # Diretório base para resultados
IMAGES_DIR="imagens"       # Diretório para gráficos

# Configurações de Plotagem
PLOT_COLORS=("blue" "red" "green" "orange" "purple")
PLOT_STYLES=("-" "--" "-." ":" "-")
PLOT_DPI=300              # Resolução dos gráficos

# Configurações de Análise
RTT_BASELINE=20           # RTT baseline esperado (ms)
BUFFERBLOAT_THRESHOLD=50  # Threshold para considerar bufferbloat (ms acima do baseline)

# Configurações do Sistema
CLEANUP_TIMEOUT=30        # Timeout para limpeza de processos (segundos)
MAX_RETRIES=3            # Número máximo de tentativas em caso de falha

# Comentários sobre os parâmetros:
# 
# NETWORK_BANDWIDTH: Simula um link ADSL típico. Valores comuns:
#   - 1.5 Mbps: ADSL básico
#   - 10 Mbps: Internet banda larga residencial
#   - 100 Mbps: Fibra ótica
#
# NETWORK_DELAY: Simula diferentes distâncias/latências. Valores comuns:
#   - 10 ms: Conexão local/metropolitana
#   - 50 ms: Conexão nacional
#   - 100 ms: Conexão internacional
#
# BUFFER_SIZE_LARGE: Buffer grande pode causar bufferbloat
# BUFFER_SIZE_SMALL: Buffer pequeno pode causar perdas
#
# Regra geral: Buffer = Bandwidth * Delay
# Para 1.5 Mbps e 20 ms RTT: ~4 pacotes seria ideal
# 100 pacotes = 25x maior que o ideal (muito grande)
# 20 pacotes = 5x maior que o ideal (ainda grande mas melhor)
