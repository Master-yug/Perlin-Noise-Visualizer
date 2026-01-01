import random
import math
import pygame
import sys
import json
import time
import numpy as np
from pygame.locals import *

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Generative Flow Field Studio")

clock = pygame.time.Clock()

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.field = []
        self.noise_scale = 0.1
        self.particle_speed = 1.0
        self.max_particles = 1000
        self.trail_length = 50
        self.color_mode = 0
        self.grid_size = 20
        
        for i in range(self.max_particles):
            self.particles.append({
                'x': random.random() * SCREEN_WIDTH,
                'y': random.random() * SCREEN_HEIGHT,
                'vx': 0,
                'vy': 0,
                'age': 0,
                'history': [],
                'color': (255, 255, 255)
            })
        
        for x in range(self.grid_size):
            self.field.append([])
            for y in range(self.grid_size):
                angle = random.random() * 2 * math.pi
                self.field[x].append({
                    'angle': angle,
                    'vx': math.cos(angle),
                    'vy': math.sin(angle)
                })
    
    def update_field(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                nx = x * 0.1 * self.noise_scale
                ny = y * 0.1 * self.noise_scale
                angle = random.random() * 2 * math.pi
                self.field[x][y]['angle'] = angle
                self.field[x][y]['vx'] = math.cos(angle) * self.particle_speed
                self.field[x][y]['vy'] = math.sin(angle) * self.particle_speed
    
    def update_particles(self):
        for particle in self.particles:
            grid_x = int(particle['x'] / SCREEN_WIDTH * self.grid_size)
            grid_y = int(particle['y'] / SCREEN_HEIGHT * self.grid_size)
            
            if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
                field_cell = self.field[grid_x][grid_y]
                particle['vx'] = field_cell['vx'] * random.random()
                particle['vy'] = field_cell['vy'] * random.random()
            
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            if particle['x'] < 0:
                particle['x'] = SCREEN_WIDTH
            if particle['x'] > SCREEN_WIDTH:
                particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = SCREEN_HEIGHT
            if particle['y'] > SCREEN_HEIGHT:
                particle['y'] = 0
            
            particle['history'].append((particle['x'], particle['y']))
            if len(particle['history']) > self.trail_length:
                particle['history'] = particle['history'][1:]
            
            particle['age'] += 1
            if self.color_mode == 0:
                particle['color'] = (255, 255, 255)
            elif self.color_mode == 1:
                particle['color'] = (100, 200, 255)
            else:
                particle['color'] = (255, 100, 200)
    
    def draw(self, surface):
        for particle in self.particles:
            if len(particle['history']) > 1:
                for i in range(len(particle['history']) - 1):
                    start_pos = particle['history'][i]
                    end_pos = particle['history'][i + 1]
                    alpha = 255 - i * 5
                    color = (particle['color'][0], particle['color'][1], particle['color'][2])
                    pygame.draw.line(surface, color, start_pos, end_pos, 1)

class UIControl:
    def __init__(self, x, y, width, height, label, min_val, max_val, value):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.dragging = False
    
    def draw(self, surface):
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)
        
        font = pygame.font.SysFont('Arial', 16)
        label_text = font.render(f"{self.label}: {self.value:.2f}", True, (255, 255, 255))
        surface.blit(label_text, (self.rect.x + 10, self.rect.y - 25))
        
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        pygame.draw.circle(surface, (255, 100, 100), (int(handle_x), self.rect.centery), 8)
    
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
        elif event.type == MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == MOUSEMOTION:
            if self.dragging:
                self.update_value(event.pos[0])
    
    def update_value(self, mouse_x):
        relative_x = max(0, min(self.rect.width, mouse_x - self.rect.x))
        self.value = self.min_val + (relative_x / self.rect.width) * (self.max_val - self.min_val)

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = (80, 80, 80)
        self.hover_color = (100, 100, 100)
        self.current_color = self.color
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        
        font = pygame.font.SysFont('Arial', 18)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
            else:
                self.current_color = self.color
        
        if event.type == MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

particle_system = ParticleSystem()

controls = [
    UIControl(50, 150, 300, 20, "Noise Scale", 0.01, 0.5, 0.1),
    UIControl(50, 220, 300, 20, "Particle Speed", 0.1, 5.0, 1.0),
    UIControl(50, 290, 300, 20, "Particle Count", 100, 5000, 1000),
    UIControl(50, 360, 300, 20, "Trail Length", 10, 200, 50),
]

buttons = [
    Button(50, 450, 140, 40, "Randomize"),
    Button(210, 450, 140, 40, "Export PNG"),
    Button(50, 510, 140, 40, "Color 1"),
    Button(210, 510, 140, 40, "Color 2"),
]

def save_screenshot():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"flow_field_{timestamp}.png"
    pygame.image.save(screen, filename)
    print(f"Saved screenshot as {filename}")

def randomize_parameters():
    for control in controls:
        control.value = random.uniform(control.min_val, control.max_val)
    particle_system.noise_scale = controls[0].value
    particle_system.particle_speed = controls[1].value
    particle_system.max_particles = int(controls[2].value)
    particle_system.trail_length = int(controls[3].value)
    particle_system.update_field()

def handle_button_click(button_text):
    if button_text == "Randomize":
        randomize_parameters()
    elif button_text == "Export PNG":
        save_screenshot()
    elif button_text == "Color 1":
        particle_system.color_mode = 0
    elif button_text == "Color 2":
        particle_system.color_mode = 1

def draw_background():
    screen.fill((20, 20, 30))
    
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, (30, 30, 40), (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, (30, 30, 40), (0, y), (SCREEN_WIDTH, y), 1)

def draw_ui():
    font = pygame.font.SysFont('Arial', 32)
    title = font.render("Generative Flow Field Studio", True, (255, 255, 255))
    screen.blit(title, (50, 50))
    
    for control in controls:
        control.draw(screen)
    
    for button in buttons:
        button.draw(screen)
    
    font_small = pygame.font.SysFont('Arial', 14)
    instructions = [
        "Controls:",
        "- Adjust sliders to change parameters",
        "- Click Randomize for new configuration",
        "- Export PNG to save your creation",
        "- Particles follow Perlin noise field"
    ]
    
    for i, line in enumerate(instructions):
        text = font_small.render(line, True, (200, 200, 200))
        screen.blit(text, (SCREEN_WIDTH - 250, 100 + i * 25))

running = True
last_update = time.time()

while running:
    current_time = time.time()
    
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_s:
                save_screenshot()
            elif event.key == K_r:
                randomize_parameters()
        
        for control in controls:
            control.handle_event(event)
        
        for button in buttons:
            if button.handle_event(event):
                handle_button_click(button.text)
    
    if current_time - last_update > 0.016:
        particle_system.noise_scale = controls[0].value
        particle_system.particle_speed = controls[1].value
        new_max = int(controls[2].value)
        
        if new_max != particle_system.max_particles:
            if new_max > particle_system.max_particles:
                for i in range(new_max - particle_system.max_particles):
                    particle_system.particles.append({
                        'x': random.random() * SCREEN_WIDTH,
                        'y': random.random() * SCREEN_HEIGHT,
                        'vx': 0,
                        'vy': 0,
                        'age': 0,
                        'history': [],
                        'color': (255, 255, 255)
                    })
            else:
                particle_system.particles = particle_system.particles[:new_max]
            particle_system.max_particles = new_max
        
        particle_system.trail_length = int(controls[3].value)
        
        particle_system.update_field()
        particle_system.update_particles()
        last_update = current_time
    
    draw_background()
    particle_system.draw(screen)
    draw_ui()
    
    fps_text = pygame.font.SysFont('Arial', 16).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(fps_text, (SCREEN_WIDTH - 100, 20))
    
    particle_text = pygame.font.SysFont('Arial', 16).render(f"Particles: {len(particle_system.particles)}", True, (255, 255, 255))
    screen.blit(particle_text, (SCREEN_WIDTH - 150, 50))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
