// Entity Model base
class Entity{
    constructor(id,x,y,sizex,sizey,texture){
        this.id = id;
        this.posx = x;
        this.posy = y;
        this.sizex = sizex;
        this.sizey = sizey;
        this.texture = texture;
        this.velx = 0;
        this.vely = 0;
        this.decposx = 0;
        this.decposy = 0;

    }
    move(x,y,map){
        let can_move = true;
        for(let dy = 0;dy<this.sizey;dy++){
            for(let dx = 0;dx<this.sizex;dx++){
                let col = map.check_col(this.posx + x + dx, this.posy + y + dy, 0);
                let col2 = map.check_col(this.posx + x + dx, this.posy + y + dy, 1);
                if(col ==1 || col2 == 1){
                    can_move = false;
                }
            }
            if(!can_move) break;

        }
        if(can_move){
            this.posx += x;
            this.posy += y;
        }
    }
    collision(x,y){
        return (this.posx <= x < this.posx + this.sizex && this.posy <= y < this.posy + this.sizey)

    }
    run(map) {
        if (this.stats && typeof this.stats.update_effects === "function") {
            this.stats.update_effects();
        }
        if (this.behavior && typeof this.behavior.run === "function") {
            this.behavior.run(this, map);
        }
    }
    kill(){

    }
}
class EControl{
    constructor() {
        this.Entities = []; 
    }
    add(e){
        e.id = this.Entities.length;
        this.Entities.push(e);
    }
    rem(id){
        for (let i = 0; i < this.Entities.length; i++) {
            if (this.Entities[i].id === id) {
                this.Entities.splice(i, 1);
                break;
            }
        }   
    }
    run(map){
        for (let i = 0; i < this.Entities.length; i++) {
            this.Entities[i].run(map);
        }
    }
}
export { Entity, EControl };