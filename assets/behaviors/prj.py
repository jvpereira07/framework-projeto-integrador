def fun1(entity, map, dirx, diry, EControl):
    
    if not hasattr(entity, "already_hit"):
        entity.already_hit = []

    if entity.time > 0:
        # Movimento do projétil
        entity.posx += dirx * entity.speed
        entity.posy += diry * entity.speed
        entity.time -= 1

        # Verifica colisão com entidades (exceto ele mesmo e os já atingidos)
        from core.entity import EControl
        for other in EControl.Entities:
            if other.id == entity.id or other.id in entity.already_hit:
                continue  # ignora ele mesmo e quem já foi atingido

            if abs(entity.posx - other.posx) < entity.sizex and abs(entity.posy - other.posy) < entity.sizey:
                if other.type == "mob":
                    other.take_damage(entity.damage)
                    entity.penetration -= 1
                    entity.already_hit.append(other.id)

                    if entity.penetration <= 0:
                        entity.kill()

                break
    else:
        entity.kill()


def wave_motion(entity, map, dirx, diry, EControl):
    """
    Comportamento de projétil com movimento ondulatório (senoidal).
    O projétil se move em linha reta enquanto oscila perpendicularmente
    em um padrão de onda com comprimento estendido.
    """
    import math
    
    if not hasattr(entity, "already_hit"):
        entity.already_hit = []
    
    # Inicializa propriedades da onda na primeira execução
    if not hasattr(entity, "wave_initialized"):
        entity.wave_initialized = True
        entity.wave_phase = 0.0  # Fase atual da onda (em radianos)
        entity.wave_frequency = 0.07  # Frequência da onda (menor = onda mais longa)
        entity.wave_amplitude = 40.0  # Amplitude da onda (distância do centro)
        
        # Salva a direção principal normalizada
        magnitude = math.sqrt(dirx**2 + diry**2)
        if magnitude > 0:
            entity.main_dirx = dirx / magnitude
            entity.main_diry = diry / magnitude
        else:
            entity.main_dirx = 1.0
            entity.main_diry = 0.0
        
        # Calcula vetor perpendicular para a oscilação
        # Se direção é (x, y), perpendicular é (-y, x)
        entity.perp_dirx = -entity.main_diry
        entity.perp_diry = entity.main_dirx
        
        # Posição base (sem oscilação)
        entity.base_posx = entity.posx
        entity.base_posy = entity.posy

    if entity.time > 0:
        # Atualiza fase da onda
        entity.wave_phase += entity.wave_frequency
        
        # Calcula offset senoidal perpendicular à direção principal
        wave_offset = math.sin(entity.wave_phase) * entity.wave_amplitude
        
        # Move na direção principal
        entity.base_posx += entity.main_dirx * entity.speed
        entity.base_posy += entity.main_diry * entity.speed
        
        # Aplica oscilação perpendicular
        entity.posx = entity.base_posx + entity.perp_dirx * wave_offset
        entity.posy = entity.base_posy + entity.perp_diry * wave_offset
        
        entity.time -= 1

        # Verifica colisão com entidades (exceto ele mesmo e os já atingidos)
        from core.entity import EControl
        for other in EControl.Entities:
            # Ignora a si próprio e o dono do projétil
            is_owner = (hasattr(entity, 'id_owner') and hasattr(entity, 'type_owner') and
                        getattr(other, 'id', None) == getattr(entity, 'id_owner', None) and
                        getattr(other, 'type', None) == getattr(entity, 'type_owner', None))
            if other.id == entity.id or other.id in entity.already_hit or is_owner:
                continue  # ignora ele mesmo e quem já foi atingido

            # Verifica colisão por hitbox
            if (entity.posx < other.posx + other.sizex and
                entity.posx + entity.sizex > other.posx and
                entity.posy < other.posy + other.sizey and
                entity.posy + entity.sizey > other.posy):
                
                if other.type == "mob" and hasattr(other, 'stats'):
                    other.take_damage(entity.damage)
                    entity.penetration -= 1
                    entity.already_hit.append(other.id)

                    if entity.penetration <= 0:
                        entity.kill()
                        return

    else:
        entity.kill()


def spiral_motion(entity, map, dirx, diry, EControl):
    """
    Comportamento de projétil com movimento espiral.
    O projétil gira em espiral enquanto avança, com raio crescente.
    """
    import math
    
    if not hasattr(entity, "already_hit"):
        entity.already_hit = []
    
    # Inicializa propriedades da espiral
    if not hasattr(entity, "spiral_initialized"):
        entity.spiral_initialized = True
        entity.spiral_angle = 1.0
        entity.spiral_radius = 5.0  # Raio inicial pequeno
        entity.spiral_radius_growth = 0.4  # Quanto o raio cresce por frame
        entity.spiral_rotation_speed = 0.05  # Velocidade de rotação
        
        # Direção principal
        magnitude = math.sqrt(dirx**2 + diry**2)
        if magnitude > 0:
            entity.main_dirx = dirx / magnitude
            entity.main_diry = diry / magnitude
        else:
            entity.main_dirx = 1.0
            entity.main_diry = 0.0
        
        # Posição central
        entity.center_posx = entity.posx
        entity.center_posy = entity.posy

    if entity.time > 0:
        # Move o centro na direção principal
        entity.center_posx += entity.main_dirx * entity.speed * 0.7
        entity.center_posy += entity.main_diry * entity.speed * 0.7
        
        # Atualiza ângulo e raio
        entity.spiral_angle += entity.spiral_rotation_speed
        entity.spiral_radius += entity.spiral_radius_growth
        
        # Calcula posição em espiral
        offset_x = math.cos(entity.spiral_angle) * entity.spiral_radius
        offset_y = math.sin(entity.spiral_angle) * entity.spiral_radius
        
        entity.posx = entity.center_posx + offset_x
        entity.posy = entity.center_posy + offset_y
        
        entity.time -= 1

        # Verifica colisão
        from core.entity import EControl
        for other in EControl.Entities:
            if other.id == entity.id or other.id in entity.already_hit:
                continue

            if (entity.posx < other.posx + other.sizex and
                entity.posx + entity.sizex > other.posx and
                entity.posy < other.posy + other.sizey and
                entity.posy + entity.sizey > other.posy):
                
                if other.type == "mob" and hasattr(other, 'stats'):
                    other.take_damage(entity.damage)
                    entity.penetration -= 1
                    entity.already_hit.append(other.id)

                    if entity.penetration <= 0:
                        entity.kill()
                        return

    else:
        entity.kill()


projectiles_behaviors = {
    "teste": fun1,
    "wave": wave_motion,
    "spiral": spiral_motion
}