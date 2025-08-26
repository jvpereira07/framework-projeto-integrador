def fun1(entity, map, dirx, diry, EControl):
    
    if not hasattr(entity, "already_hit"):
        entity.already_hit = []

    if entity.time > 0:
        # Movimento do projétil
        entity.posx += dirx * entity.speed
        entity.posy += diry * entity.speed
        entity.time -= 1

        # Verifica colisão com entidades (exceto ele mesmo e os já atingidos)
        for other in EControl.Entities:
            if other.id == entity.id or other.id in entity.already_hit:
                continue  # ignora ele mesmo e quem já foi atingido

            if abs(entity.posx - other.posx) < entity.sizex and abs(entity.posy - other.posy) < entity.sizey:
                if other.type == "mob":
                    other.stats.hp -= entity.damage
                    entity.penetration -= 1
                    entity.already_hit.append(other.id)

                    if entity.penetration <= 0:
                        entity.kill()

                break

    else:
        entity.kill()




projectiles_behaviors = {
    "teste": fun1
}