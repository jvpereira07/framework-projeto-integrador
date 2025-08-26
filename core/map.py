import pygame
import json
import numpy as np
import sqlite3
from OpenGL.GL import *


def load_texture(path):
    image = pygame.image.load(path).convert_alpha()
    # Inverte verticalmente para o padrão do OpenGL
    image = pygame.transform.flip(image, False, True)
    image_data = pygame.image.tostring(image, "RGBA", True)
    width, height = image.get_size()
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    return texture_id, width, height

class Layer:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Map:
    def __init__(self, filename, tileset_img):
        with open(filename) as f:
            self.map_data = json.load(f)
        
        self.tilewidth = self.map_data["tilewidth"]
        self.tileheight = self.map_data["tileheight"]
        self.map_width = self.map_data["width"]
        self.map_height = self.map_data["height"]
        
        # Carrega o tileset como textura OpenGL
        self.tileset_id, self.tileset_width, self.tileset_height = load_texture(tileset_img)
        self.tileset_cols = self.tileset_width // self.tilewidth
        
        # Processa as camadas do mapa
        self.layers = []
        for layer_data in self.map_data["layers"]:
            if layer_data["type"] == "tilelayer":
                layer = Layer(layer_data["id"], layer_data["name"])
                self.layers.append({
                    "data": layer_data,
                    "object": layer
                })
        
        # Cria uma matriz 3D com os dados dos tiles
        self.matriz = np.zeros((len(self.layers), self.map_height, self.map_width), dtype=int)
        for i, layer in enumerate(self.layers):
            data = layer["data"]["data"]
            self.matriz[i] = np.array(data).reshape(self.map_height, self.map_width)
        
        # Carrega dados de colisão a partir de um banco SQLite
        conn = sqlite3.connect("assets/data/data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tile")
        self.col = {row[0]: row[2] for row in cursor.fetchall()}
        conn.close()
    
    def check_col(self, x, y, layer):
        tile_x = x // self.tilewidth
        tile_y = y // self.tileheight
        
        if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
            tile_id = self.matriz[layer, tile_y, tile_x]
            return self.col.get(tile_id)
        return None
    
    def render(self, camera_x=0, camera_y=0, zoom=1.0, player=None, screen_width =1920,screen_height = 1080):
        zoom = max(0.1, zoom)
        # Definindo uma área visível (aqui os valores de tela estão "hard-coded", mas podem ser parametrizados)
        
        if player:
            camera_x = player.posx - (screen_width / zoom) / 2
            camera_y = player.posy - (screen_height / zoom) / 2
        
        visible_tiles_x = int((screen_width / zoom) // self.tilewidth) + 2
        visible_tiles_y = int((screen_height / zoom) // self.tileheight) + 2
        
        start_x = max(0, int(camera_x // self.tilewidth))
        end_x = min(self.map_width, start_x + visible_tiles_x)
        
        start_y = max(0, int(camera_y // self.tileheight))
        end_y = min(self.map_height, start_y + visible_tiles_y)
        
        scaled_width = int(self.tilewidth * zoom)
        scaled_height = int(self.tileheight * zoom)
        
        glBindTexture(GL_TEXTURE_2D, self.tileset_id)
        glBegin(GL_QUADS)
        for layer_index, layer in enumerate(self.layers):
            if not layer["data"].get("visible", True):
                continue
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    tile_gid = layer["data"]["data"][y * self.map_width + x]
                    if tile_gid == 0:
                        continue
                    tile_id = tile_gid - 1
                    tileset_x = (tile_id % self.tileset_cols) * self.tilewidth
                    tileset_y = (tile_id // self.tileset_cols) * self.tileheight
                    
                    # Converte coordenadas de textura para o intervalo [0, 1]
                    tx1 = tileset_x / self.tileset_width
                    ty1 = tileset_y / self.tileset_height
                    tx2 = (tileset_x + self.tilewidth) / self.tileset_width
                    ty2 = (tileset_y + self.tileheight) / self.tileset_height
                    
                    screen_x = (x * self.tilewidth - camera_x) * zoom
                    screen_y = (y * self.tileheight - camera_y) * zoom
                    
                    glTexCoord2f(tx1, ty1); glVertex2f(screen_x, screen_y)
                    glTexCoord2f(tx2, ty1); glVertex2f(screen_x + scaled_width, screen_y)
                    glTexCoord2f(tx2, ty2); glVertex2f(screen_x + scaled_width, screen_y + scaled_height)
                    glTexCoord2f(tx1, ty2); glVertex2f(screen_x, screen_y + scaled_height)
        glEnd()
    
    def close(self):
        glDeleteTextures([self.tileset_id])
