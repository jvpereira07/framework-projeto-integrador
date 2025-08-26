#!/usr/bin/env python3
"""
Framework - Projeto Integrador
Ponto de entrada principal
"""

import sys
import os

# Adiciona o diretório atual ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Função principal do jogo"""
    try:
        # Importa e inicia o jogo
        from core.game import Game
        
        print("Iniciando Framework - Projeto Integrador...")
        game = Game()
        game.run()
        
    except ImportError as e:
        print(f"Erro de importação: {e}")
        print("Verifique se todas as dependências estão instaladas.")
        return 1
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
