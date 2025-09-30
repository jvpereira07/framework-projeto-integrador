import fs from 'fs/promises';
import sqlite3 from 'sqlite3';

/**
 * A classe Map no lado do servidor é responsável por carregar os dados de colisão do mapa.
 * A lógica de renderização é omitida, pois é exclusiva do cliente.
 */
class Map {
    constructor() {
        this.map_data = null;
        this.tilewidth = 0;
        this.tileheight = 0;
        this.map_width = 0;
        this.map_height = 0;
        this.layers = [];
        this.matriz = []; // Matriz 3D simplificada com dados dos tiles
        this.col = {}; // Dicionário de colisão (tile_id -> 1 se colide)
    }

    /**
     * Carrega os dados do mapa a partir de um arquivo JSON.
     * @param {string} filePath - Caminho para o arquivo .json do mapa.
     */
    async _loadMapData(filePath) {
        try {
            const data = await fs.readFile(filePath, 'utf8');
            this.map_data = JSON.parse(data);

            this.tilewidth = this.map_data.tilewidth;
            this.tileheight = this.map_data.tileheight;
            this.map_width = this.map_data.width;
            this.map_height = this.map_data.height;

            // Processa as camadas do mapa
            this.layers = this.map_data.layers
                .filter(layer => layer.type === "tilelayer")
                .map(layer => ({ id: layer.id, name: layer.name, data: layer.data }));

            // Cria a matriz 3D com os dados dos tiles
            this.matriz = new Array(this.layers.length);
            for (let i = 0; i < this.layers.length; i++) {
                this.matriz[i] = this.layers[i].data;
            }

        } catch (error) {
            console.error(`Erro ao carregar o arquivo do mapa: ${error.message}`);
            throw error;
        }
    }

    /**
     * Carrega os dados de colisão do banco de dados SQLite.
     * @param {string} dbPath - Caminho para o arquivo .db do banco de dados.
     */
    async _loadCollisionData(dbPath) {
        return new Promise((resolve, reject) => {
            const db = new (sqlite3.verbose().Database)(dbPath, sqlite3.OPEN_READONLY, (err) => {
                if (err) {
                    console.error(`Erro ao conectar ao banco de dados: ${err.message}`);
                    return reject(err);
                }
            });

            db.all("SELECT * FROM tile", [], (err, rows) => {
                if (err) {
                    console.error(`Erro ao consultar a tabela 'tile': ${err.message}`);
                    db.close();
                    return reject(err);
                }
                
                // Popula o objeto de colisão
                this.col = rows.reduce((acc, row) => {
                    acc[row.id] = row.col;
                    return acc;
                }, {});

                db.close();
                resolve();
            });
        });
    }

    /**
     * Verifica se há colisão em uma coordenada (x, y) em uma camada específica.
     * @param {number} x - Coordenada X no mundo.
     * @param {number} y - Coordenada Y no mundo.
     * @param {number} layer - O índice da camada a ser verificada.
     * @returns {number|null} Retorna 1 se houver colisão, 0 se não houver, ou null se fora do mapa.
     */
    check_col(x, y, layer) {
        const tile_x = Math.floor(x / this.tilewidth);
        const tile_y = Math.floor(y / this.tileheight);

        if (tile_x >= 0 && tile_x < this.map_width && tile_y >= 0 && tile_y < this.map_height) {
            if (this.matriz[layer]) {
                const tile_id = this.matriz[layer][tile_y * this.map_width + tile_x];
                return this.col[tile_id] || 0; // Retorna 0 se o tile não estiver no dicionário de colisão
            }
        }
        return null; // Fora dos limites do mapa
    }
    
    /**
     * Cria e retorna uma matriz 2D de colisão para pathfinding.
     * Um tile é bloqueado (1) se qualquer camada tiver um tile de colisão.
     * @returns {Array<Array<number>>} Matriz 2D com 0 para livre e 1 para bloqueado.
     */
    get_collision_matrix() {
        const rows = this.map_height;
        const cols = this.map_width;
        const matrix = Array(rows).fill(0).map(() => Array(cols).fill(0));

        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                let blocked = 0;
                for (let l = 0; l < this.layers.length; l++) {
                    const tile_id = this.matriz[l][y * this.map_width + x];
                    if (this.col[tile_id]) {
                        blocked = 1;
                        break;
                    }
                }
                matrix[y][x] = blocked;
            }
        }
        return matrix;
    }


    /**
     * Factory function para criar e inicializar um objeto Map de forma assíncrona.
     * @param {string} mapPath - Caminho para o arquivo .json do mapa.
     * @param {string} dbPath - Caminho para o arquivo .db do banco de dados.
     * @returns {Promise<Map>} Uma promessa que resolve para uma instância de Mapa totalmente carregada.
     */
    static async create(mapPath, dbPath) {
        const map = new Map();
        await map._loadMapData(mapPath);
        await map._loadCollisionData(dbPath);
        console.log("Mapa e dados de colisão carregados no servidor.");
        return map;
    }
}

export default Map;