#!/usr/bin/env python3
"""Teste para verificar a lógica do efeito de dano"""

def test_damage_effect():
    # Simula os parâmetros da entidade
    damage_effect_duration = 0.8
    damage_max_blinks = 4
    damage_blink_interval = 0.2
    
    print("Testando efeito de dano:")
    print(f"Duração total: {damage_effect_duration}s")
    print(f"Intervalos de piscada: {damage_blink_interval}s")
    print(f"Máximo de piscadas: {damage_max_blinks}")
    print()
    
    # Simula o tempo passando
    for i in range(50):  # 50 frames simulados
        time_step = i * (1/60)  # Assume 60 FPS
        damage_effect_timer = damage_effect_duration - time_step
        
        if damage_effect_timer <= 0:
            should_render = False
        else:
            elapsed_time = damage_effect_duration - damage_effect_timer
            blink_cycle = int(elapsed_time / damage_blink_interval)
            
            if blink_cycle < damage_max_blinks:
                should_render = blink_cycle % 2 == 0
            else:
                should_render = False
        
        if time_step <= damage_effect_duration + 0.1:  # Mostra um pouco além do tempo
            status = "VERMELHO" if should_render else "NORMAL"
            print(f"Frame {i:2d}: Tempo {time_step:.3f}s -> {status}")

if __name__ == "__main__":
    test_damage_effect()
