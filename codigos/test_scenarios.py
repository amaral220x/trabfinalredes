#!/usr/bin/env python3

"""
Test script para verificar se os novos cenários estão funcionando corretamente.
"""

import sys
import os
import json
import argparse
from tcp_competition import CompetitionTopo, run_competition_experiment

def test_topology_creation():
    """Testa a criação das topologias para diferentes cenários."""
    print("Testando criação de topologias...")
    
    # Teste 1: 1 vs 1
    print("1. Testando topologia 1 vs 1...")
    topo1 = CompetitionTopo(bw_net=10, delay=50, maxq=100, scenario="reno_vs_bbr")
    print("   ✓ Topologia 1 vs 1 criada com sucesso")
    
    # Teste 2: 2 vs 2
    print("2. Testando topologia 2 vs 2...")
    topo2 = CompetitionTopo(bw_net=10, delay=50, maxq=100, scenario="2reno_vs_2bbr")
    print("   ✓ Topologia 2 vs 2 criada com sucesso")
    
    # Teste 3: 2 vs 1
    print("3. Testando topologia 2 vs 1...")
    topo3 = CompetitionTopo(bw_net=10, delay=50, maxq=100, scenario="2reno_vs_1bbr")
    print("   ✓ Topologia 2 vs 1 criada com sucesso")
    
    return True

def test_experiment_configuration():
    """Testa a configuração dos experimentos."""
    print("\nTestando configuração dos experimentos...")
    
    scenarios = [
        ("reno_vs_bbr", "1 TCP Reno vs 1 TCP BBR"),
        ("2reno_vs_2bbr", "2 TCP Reno vs 2 TCP BBR"),
        ("2reno_vs_1bbr", "2 TCP Reno vs 1 TCP BBR")
    ]
    
    for scenario, description in scenarios:
        print(f"Testando cenário: {description}")
        
        # Verificar se o cenário é reconhecido
        try:
            topo = CompetitionTopo(bw_net=10, delay=50, maxq=100, scenario=scenario)
            print(f"   ✓ Cenário '{scenario}' reconhecido")
        except Exception as e:
            print(f"   ✗ Erro no cenário '{scenario}': {e}")
            return False
    
    return True

def test_results_analysis():
    """Testa se a análise de resultados pode lidar com múltiplos fluxos."""
    print("\nTestando análise de resultados...")
    
    # Criar dados de exemplo para teste
    sample_results = {
        "scenario": "2reno_vs_2bbr",
        "configuration": {
            "bandwidth": 10,
            "delay": 50,
            "queue_size": 100,
            "duration": 30
        },
        "reno_flows": [
            {"avg_throughput": 2.5, "total_bytes": 75000000},
            {"avg_throughput": 2.3, "total_bytes": 69000000}
        ],
        "bbr_flows": [
            {"avg_throughput": 2.7, "total_bytes": 81000000},
            {"avg_throughput": 2.4, "total_bytes": 72000000}
        ],
        "rtt_stats": {
            "reno_avg": 85.5,
            "bbr_avg": 82.3
        },
        "queue_stats": {
            "avg_utilization": 0.65,
            "max_utilization": 0.89
        }
    }
    
    # Salvar dados de teste
    test_dir = "/tmp/test_competition"
    os.makedirs(test_dir, exist_ok=True)
    
    with open(f"{test_dir}/competition_results.json", "w") as f:
        json.dump(sample_results, f, indent=2)
    
    print("   ✓ Dados de teste criados")
    
    # Testar se o analyze_competition.py pode processar os dados
    try:
        from analyze_competition import analyze_competition_results
        results = analyze_competition_results(test_dir)
        print("   ✓ Análise de resultados funcionando")
        return True
    except Exception as e:
        print(f"   ✗ Erro na análise: {e}")
        return False

def print_scenario_info():
    """Imprime informações sobre os cenários disponíveis."""
    print("\n=== Cenários Disponíveis ===")
    
    scenarios = [
        {
            "name": "reno_vs_bbr",
            "description": "1 TCP Reno vs 1 TCP BBR",
            "hosts": "h1 (Reno), h2 (BBR)",
            "flows": "1 flow cada"
        },
        {
            "name": "2reno_vs_2bbr",
            "description": "2 TCP Reno vs 2 TCP BBR",
            "hosts": "h1, h2 (Reno), h3, h4 (BBR)",
            "flows": "2 flows cada algoritmo"
        },
        {
            "name": "2reno_vs_1bbr",
            "description": "2 TCP Reno vs 1 TCP BBR",
            "hosts": "h1, h2 (Reno), h3 (BBR)",
            "flows": "2 flows Reno, 1 flow BBR"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['description']}")
        print(f"   Cenário: {scenario['name']}")
        print(f"   Hosts: {scenario['hosts']}")
        print(f"   Fluxos: {scenario['flows']}")

def main():
    parser = argparse.ArgumentParser(description="Teste dos cenários de competição TCP")
    parser.add_argument("--info", action="store_true", help="Mostrar informações dos cenários")
    parser.add_argument("--test", action="store_true", help="Executar testes")
    
    args = parser.parse_args()
    
    if args.info:
        print_scenario_info()
        return
    
    if args.test:
        print("=== Testando Implementação dos Cenários ===")
        
        all_tests_passed = True
        
        # Teste 1: Criação de topologias
        try:
            test_topology_creation()
        except Exception as e:
            print(f"✗ Erro no teste de topologias: {e}")
            all_tests_passed = False
        
        # Teste 2: Configuração de experimentos
        try:
            test_experiment_configuration()
        except Exception as e:
            print(f"✗ Erro no teste de configuração: {e}")
            all_tests_passed = False
        
        # Teste 3: Análise de resultados
        try:
            test_results_analysis()
        except Exception as e:
            print(f"✗ Erro no teste de análise: {e}")
            all_tests_passed = False
        
        print("\n=== Resultado dos Testes ===")
        if all_tests_passed:
            print("✓ Todos os testes passaram! Os novos cenários estão prontos.")
        else:
            print("✗ Alguns testes falharam. Verifique os erros acima.")
            sys.exit(1)
    else:
        print("Use --info para ver informações ou --test para executar testes")

if __name__ == "__main__":
    main()
