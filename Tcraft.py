import tkinter as tk
from tkinter import messagebox
import random
import math
import time


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b)))
    )

def lerp_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1 + (r2 - r1) * t,
                      g1 + (g2 - g1) * t,
                      b1 + (b2 - b1) * t)

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))



BLOCK_DEF = {
    
    'air':     ('#87ceeb', '#0d1b2a', 'sky'),
    'grass':   ('#27ae60', '#1a4a2e', 'grass'),
    'dirt':    ('#795548', '#3d2a22', 'dirt'),
    'stone':   ('#95a5a6', '#3a4a4b', 'stone'),
    'coal':    ('#2c3e50', '#111820', 'coal'),
    'wood':    ('#5d4037', '#2a1c17', 'wood'),
    'leaf':    ('#2ecc71', '#0d5c30', 'leaf'),
    'bedrock': ('#1a1a1a', '#0a0a0a', 'bedrock'),
    'planks':  ('#d35400', '#6b2a00', 'planks'),
    'sand':    ('#f0d080', '#7a6830', 'sand'),
    'water':   ('#1a78c2', '#0a3060', 'water'),
}

SKY_DAY   = '#87ceeb'
SKY_NIGHT = '#0d1b2a'
SKY_DAWN  = '#ff7043'


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'canvas_id')

    def __init__(self, x, y, color, canvas):
        self.x  = x
        self.y  = y
        angle   = random.uniform(0, math.tau)
        speed   = random.uniform(1.5, 5.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2.0
        self.max_life = random.randint(18, 35)
        self.life     = self.max_life
        self.color    = color
        self.size     = random.uniform(3, 7)
        s = self.size
        self.canvas_id = canvas.create_rectangle(
            x - s, y - s, x + s, y + s,
            fill=color, outline='', tags='particle'
        )

    def update(self, canvas):
        self.vy += 0.35          
        self.vx *= 0.96          
        self.x  += self.vx
        self.y  += self.vy
        self.life -= 1
        t = self.life / self.max_life
        s = self.size * t
        canvas.coords(self.canvas_id,
                      self.x - s, self.y - s,
                      self.x + s, self.y + s)
        
        faded = lerp_color(self.color, '#000000', 1 - t)
        canvas.itemconfig(self.canvas_id, fill=faded)
        return self.life > 0


class World:
    GRID = 40

    def __init__(self, cols=120, rows=60):
        self.COLS = cols
        self.ROWS = rows
        self.grid = []        
        self.surface = []     


    def generate(self, canvas, day_factor=1.0):
        self.canvas  = canvas
        self.grid    = []
        self.surface = []

        
        def height(c):
            h  = math.sin(c * 0.08) * 4
            h += math.sin(c * 0.03) * 8
            h += math.sin(c * 0.17) * 2
            h += random.uniform(-1, 1)
            return int(12 + h)

        surf = [height(c) for c in range(self.COLS)]
        self.surface = surf

        for r in range(self.ROWS):
            row = []
            for c in range(self.COLS):
                s = surf[c]
                if r == self.ROWS - 1:
                    bt = 'bedrock'
                elif r > s + 8:
                    bt = 'coal' if random.random() < 0.08 else 'stone'
                elif r > s + 1:
                    bt = 'dirt'
                elif r == s + 1:
                    bt = 'dirt'
                elif r == s:
                    bt = 'grass'
                elif r == s - 1 and random.random() < 0.05:
                    bt = 'water'
                else:
                    bt = 'air'

                bid = self._make_block(canvas, c, r, bt, day_factor)
                row.append({'type': bt, 'id': bid})
            self.grid.append(row)

       
        occupied = set()
        for _ in range(20):
            tx = random.randint(4, self.COLS - 5)
            if tx not in occupied:
                occupied.add(tx)
                self._place_tree(canvas, tx, surf[tx] - 1, day_factor)

    

    def _block_color(self, bt, r, day_factor):
        if bt == 'air':
            return None
        day_c, night_c, _ = BLOCK_DEF[bt]
        base = lerp_color(night_c, day_c, day_factor)
        
        depth = max(0, r - 14)
        factor = max(0.25, 1 - depth * 0.04)
        rr, gg, bb = hex_to_rgb(base)
        return rgb_to_hex(rr * factor, gg * factor, bb * factor)

    def _make_block(self, canvas, c, r, bt, day_factor):
        G = self.GRID
        x0, y0 = c * G, r * G
        x1, y1 = x0 + G, y0 + G

        if bt == 'air':
            bid = canvas.create_rectangle(x0, y0, x1, y1,
                                          fill='', outline='',
                                          tags=('block', f'b_{c}_{r}'))
            return bid

        color   = self._block_color(bt, r, day_factor)
        outline = self._darken(color, 0.6)
        bid = canvas.create_rectangle(x0, y0, x1, y1,
                                      fill=color, outline=outline,
                                      tags=('block', f'b_{c}_{r}'))
        self._draw_detail(canvas, bt, x0, y0, G, color, day_factor)
        return bid

    def _darken(self, hex_color, factor=0.7):
        r, g, b = hex_to_rgb(hex_color)
        return rgb_to_hex(r * factor, g * factor, b * factor)

    def _draw_detail(self, canvas, bt, x0, y0, G, base_color, day_factor):
        """Draw procedural details on a block (dots, cracks, grain, etc.)"""
        _, mode = BLOCK_DEF[bt][0], BLOCK_DEF[bt][2]
        dark  = self._darken(base_color, 0.55)
        light = lerp_color(base_color, '#ffffff', 0.3)

        if mode == 'grass':
            
            canvas.create_rectangle(x0+1, y0+1, x0+G-1, y0+8,
                                    fill=lerp_color(base_color, '#1abc9c', 0.5),
                                    outline='', tags='detail')
            for _ in range(4):
                dx = random.randint(x0+3, x0+G-3)
                dy = random.randint(y0+10, y0+G-3)
                canvas.create_oval(dx-2, dy-2, dx+2, dy+2,
                                   fill=dark, outline='', tags='detail')

        elif mode == 'dirt':
            for _ in range(6):
                dx = random.randint(x0+3, x0+G-3)
                dy = random.randint(y0+3, y0+G-3)
                canvas.create_oval(dx-2, dy-1, dx+2, dy+1,
                                   fill=dark, outline='', tags='detail')

        elif mode == 'stone':
            
            for _ in range(2):
                sx = random.randint(x0+5, x0+G-5)
                sy = random.randint(y0+5, y0+G-5)
                ex = sx + random.randint(-8, 8)
                ey = sy + random.randint(-8, 8)
                canvas.create_line(sx, sy, ex, ey,
                                   fill=dark, width=1, tags='detail')
            
            canvas.create_oval(x0+5, y0+5, x0+11, y0+11,
                                fill=light, outline='', tags='detail')

        elif mode == 'coal':
            for _ in range(3):
                dx = random.randint(x0+4, x0+G-4)
                dy = random.randint(y0+4, y0+G-4)
                canvas.create_rectangle(dx-3, dy-3, dx+3, dy+3,
                                        fill='#aaaaaa', outline='', tags='detail')

        elif mode == 'wood':
            
            mid_y = (y0 + y0 + G) // 2
            canvas.create_line(x0+1, mid_y - 5, x0+G-1, mid_y - 5,
                                fill=dark, width=1, tags='detail')
            canvas.create_line(x0+1, mid_y + 5, x0+G-1, mid_y + 5,
                                fill=dark, width=1, tags='detail')

        elif mode == 'leaf':
            for _ in range(6):
                dx = random.randint(x0+2, x0+G-2)
                dy = random.randint(y0+2, y0+G-2)
                canvas.create_oval(dx-3, dy-3, dx+3, dy+3,
                                   fill=self._darken(base_color, 0.7),
                                   outline='', tags='detail')

        elif mode == 'planks':
            mid_x = (x0 + x0 + G) // 2
            canvas.create_line(mid_x, y0+1, mid_x, y0+G-1,
                                fill=dark, width=2, tags='detail')
            canvas.create_line(x0+1, y0+G//2, x0+G-1, y0+G//2,
                                fill=dark, width=1, tags='detail')

        elif mode == 'sand':
            for _ in range(8):
                dx = random.randint(x0+2, x0+G-2)
                dy = random.randint(y0+2, y0+G-2)
                canvas.create_oval(dx-1, dy-1, dx+1, dy+1,
                                   fill=dark, outline='', tags='detail')

        elif mode == 'bedrock':
            for _ in range(5):
                dx = random.randint(x0+3, x0+G-3)
                dy = random.randint(y0+3, y0+G-3)
                r2 = random.randint(2, 5)
                canvas.create_oval(dx-r2, dy-r2, dx+r2, dy+r2,
                                   fill='#333333', outline='', tags='detail')

        elif mode == 'water':
            
            for wy in [y0+8, y0+20, y0+32]:
                canvas.create_line(x0+2, wy, x0+G//2, wy-4, x0+G-2, wy,
                                   fill=light, smooth=True, tags='detail')

    

    def _place_tree(self, canvas, x, y, day_factor):
        for i in range(5):
            if 0 <= y - i < self.ROWS:
                self.set_block(x, y - i, 'wood', day_factor, canvas)
        for lx in range(x - 2, x + 3):
            for ly in range(y - 6, y - 1):
                if 0 <= lx < self.COLS and 0 <= ly < self.ROWS:
                    if self.grid[ly][lx]['type'] == 'air':
                        self.set_block(lx, ly, 'leaf', day_factor, canvas)

    

    def set_block(self, c, r, bt, day_factor=1.0, canvas=None):
        cv = canvas or self.canvas
        if not (0 <= c < self.COLS and 0 <= r < self.ROWS):
            return
        cell = self.grid[r][c]
        cell['type'] = bt
        G = self.GRID
        x0, y0 = c * G, r * G

        
        if bt == 'air':
            cv.itemconfig(cell['id'], fill='', outline='')
        else:
            color   = self._block_color(bt, r, day_factor)
            outline = self._darken(color, 0.6)
            cv.itemconfig(cell['id'], fill=color, outline=outline)
            
    def get(self, c, r):
        if 0 <= c < self.COLS and 0 <= r < self.ROWS:
            return self.grid[r][c]['type']
        return 'air'

    def is_solid(self, c, r):
        bt = self.get(c, r)
        return bt not in ('air', 'water', 'leaf')



class Player:
    W  = 20   
    H  = 58  
    SPEED     = 5.0
    JUMP_VEL  = -14.0
    GRAVITY   = 0.7
    MAX_FALL  = 18.0

    def __init__(self, wx, wy):
        """wx, wy are world-space coordinates (top-left of player box)."""
        self.wx   = float(wx)    
        self.wy   = float(wy)    
        self.vx   = 0.0
        self.vy   = 0.0
        self.on_ground = False

        self.hp     = 100.0
        self.hunger = 100.0
        self.max_hp = 100
        self.max_hunger = 100

        self.inventory   = {'wood': 5, 'stone': 0, 'dirt': 0, 'planks': 0, 'sand': 0, 'leaf': 0}
        self.hotbar      = ['wood', 'planks', 'stone', 'dirt']
        self.selected    = 0

       
        self.ids = {}
        self.arm_swing = 0.0
        self.face_dir  = 1   

    

    @property
    def left(self):   return self.wx
    @property
    def right(self):  return self.wx + self.W * 2
    @property
    def top(self):    return self.wy
    @property
    def bottom(self): return self.wy + self.H

    def center_world(self):
        return self.wx + self.W, self.wy + self.H / 2

    

    def update(self, keys, world):
        G = World.GRID

        
        self.vx = 0.0
        if keys.get('a') or keys.get('left'):
            self.vx = -self.SPEED
            self.face_dir = -1
        if keys.get('d') or keys.get('right'):
            self.vx = self.SPEED
            self.face_dir = 1

        
        if (keys.get('space') or keys.get('w') or keys.get('up')) and self.on_ground:
            self.vy = self.JUMP_VEL
            self.on_ground = False

        
        self.vy = min(self.vy + self.GRAVITY, self.MAX_FALL)

       

        self.wx += self.vx
        self._resolve_x(world, G)

        self.wy += self.vy
        self._resolve_y(world, G)

        
        if self.vx != 0:
            self.arm_swing += 0.25
        else:
            self.arm_swing *= 0.8

        
        self.hunger = max(0.0, self.hunger - 0.003)
        if self.hunger <= 0:
            self.hp = max(0.0, self.hp - 0.015)

    def _tiles_overlap(self, world, G):
        """Yield (c, r) of all tiles overlapping the player AABB."""
        c0 = int(self.left  // G)
        c1 = int((self.right  - 0.1) // G)
        r0 = int(self.top   // G)
        r1 = int((self.bottom - 0.1) // G)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                yield c, r

    def _resolve_x(self, world, G):
        for c, r in self._tiles_overlap(world, G):
            if world.is_solid(c, r):
                tile_l = c * G
                tile_r = tile_l + G
                if self.vx > 0:   
                    self.wx = tile_l - self.W * 2
                    self.vx = 0.0
                elif self.vx < 0: 
                    self.wx = tile_r
                    self.vx = 0.0

    def _resolve_y(self, world, G):
        self.on_ground = False
        for c, r in self._tiles_overlap(world, G):
            if world.is_solid(c, r):
                tile_t = r * G
                tile_b = tile_t + G
                if self.vy > 0:   
                    self.wy = tile_t - self.H
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0: 
                    self.wy = tile_b
                    self.vy = 0.0

   
    def add_item(self, bt):
        self.inventory[bt] = self.inventory.get(bt, 0) + 1

    def selected_item(self):
        return self.hotbar[self.selected]

    def can_place(self):
        return self.inventory.get(self.selected_item(), 0) > 0

    def consume_item(self):
        item = self.selected_item()
        self.inventory[item] -= 1



class GameEngine:
    TARGET_FPS   = 50
    TICK_MS      = 1000 // TARGET_FPS
    DAY_TICKS    = 1800          

    
    VP_PAD = 2

    def __init__(self, window):
        self.window = window
        window.title("TCraft  –  Refactored Edition")
        window.geometry("1000x860")
        window.resizable(False, False)
        window.configure(bg='#0b0c10')

        self.SCREEN_W = 1000
        self.SCREEN_H = 600

       
        self.cam_x  = 0.0  
        self.cam_y  = 0.0
        self.tcam_x = 0.0   
        self.tcam_y = 0.0
        self.CAM_LERP = 0.12

       
        self.tick_count = 0
        self.day_factor = 1.0   

        
        self.keys = {}

        
        self.notifications = []   

        
        self.particles = []

       
        self._build_canvas()
        self._build_hud()

        
        self.world  = World(cols=120, rows=60)
        self.world.generate(self.canvas, day_factor=self.day_factor)

        spawn_c = 60
        spawn_r = self.world.surface[spawn_c] - 2
        self.player = Player(
            wx = spawn_c * World.GRID - Player.W,
            wy = spawn_r * World.GRID - Player.H
        )
        self.cam_x  = self.player.wx - self.SCREEN_W / 2
        self.cam_y  = self.player.wy - self.SCREEN_H / 2
        self.tcam_x = self.cam_x
        self.tcam_y = self.cam_y

        self._create_sprites()
        self._update_hud()

        
        window.bind('<KeyPress>',   self._key_down)
        window.bind('<KeyRelease>', self._key_up)
        self.canvas.bind('<Button-1>', self._on_break)
        self.canvas.bind('<Button-3>', self._on_place)
        window.bind('<c>', lambda e: self._craft())
        window.focus_set()

        self._loop()

    

    def _build_canvas(self):
        self.canvas = tk.Canvas(
            self.window,
            width=self.SCREEN_W, height=self.SCREEN_H,
            bg=SKY_DAY, highlightthickness=0
        )
        self.canvas.pack(pady=(8, 0))

        
        self.sky_bands = []
        band_h = self.SCREEN_H // 8
        for i in range(8):
            bid = self.canvas.create_rectangle(
                0, i * band_h, self.SCREEN_W, (i + 1) * band_h,
                fill=SKY_DAY, outline='', tags='sky'
            )
            self.sky_bands.append(bid)

        
        self.sun_id  = self.canvas.create_oval(
            0, 0, 60, 60, fill='#f1c40f', outline='#f39c12', width=2, tags='sky'
        )
        self.moon_id = self.canvas.create_oval(
            0, 0, 50, 50, fill='#dcdde1', outline='#b2bec3', width=2, tags='sky'
        )

        
        self.clouds = []
        for _ in range(12):
            cx = random.randint(-200, self.SCREEN_W + 200)
            cy = random.randint(20, 130)
            w  = random.randint(80, 180)
            c_id = self.canvas.create_oval(
                cx, cy, cx + w, cy + 35,
                fill='white', outline='', tags='sky'
            )
            self.clouds.append({'id': c_id, 'wx': cx + self.cam_x, 'wy': cy + self.cam_y})

    def _build_hud(self):
        self.hud_frame = tk.Frame(self.window, bg='#1f2833', height=240)
        self.hud_frame.pack(fill='both', expand=True)

        
        self.stat_canvas = tk.Canvas(
            self.hud_frame, width=220, height=110,
            bg='#1f2833', highlightthickness=0
        )
        self.stat_canvas.pack(side='left', padx=20, pady=15, anchor='n')

       
        hb_frame = tk.Frame(self.hud_frame, bg='#1f2833')
        hb_frame.pack(side='left', expand=True, pady=10)

        tk.Label(hb_frame, text='— HOTBAR —', bg='#1f2833',
                 fg='#66fcf1', font=('Consolas', 9)).pack()
        slot_row = tk.Frame(hb_frame, bg='#1f2833')
        slot_row.pack()
        self.slot_labels = []
        for i in range(4):
            lbl = tk.Label(
                slot_row, text='', width=11, height=3,
                bg='#0b0c10', fg='#66fcf1',
                font=('Consolas', 10, 'bold'),
                highlightthickness=2,
                highlightbackground='#45a29e'
            )
            lbl.pack(side='left', padx=4)
            self.slot_labels.append(lbl)

        
        hint = (
            'WASD / Arrows – Move & Jump\n'
            'LMB – Break block\n'
            'RMB – Place block\n'
            '1-4 – Select slot\n'
            'C – Craft (wood → planks)'
        )
        tk.Label(
            self.hud_frame, text=hint,
            bg='#1f2833', fg='#888fa0',
            font=('Consolas', 9), justify='left'
        ).pack(side='right', padx=20, anchor='n', pady=15)

        

    def _create_sprites(self):
        """Create all player canvas items in screen-space (updated every frame)."""
        cx, cy = self._world_to_screen(self.player.wx + Player.W, self.player.wy)

        ids = {}
        
        ids['body']  = self.canvas.create_rectangle(
            cx - 10, cy, cx + 10, cy + 35,
            fill='#3498db', outline='#2980b9', width=2, tags='sprite'
        )
        
        ids['head']  = self.canvas.create_rectangle(
            cx - 12, cy - 25, cx + 12, cy,
            fill='#ffdbac', outline='#c9956a', width=1, tags='sprite'
        )
        
        ids['eye_l'] = self.canvas.create_oval(
            cx - 8, cy - 19, cx - 3, cy - 13,
            fill='white', outline='', tags='sprite'
        )
        ids['eye_r'] = self.canvas.create_oval(
            cx + 3, cy - 19, cx + 8, cy - 13,
            fill='white', outline='', tags='sprite'
        )
        ids['pupil_l'] = self.canvas.create_oval(
            cx - 7, cy - 18, cx - 4, cy - 14,
            fill='#1a1a2e', outline='', tags='sprite'
        )
        ids['pupil_r'] = self.canvas.create_oval(
            cx + 4, cy - 18, cx + 7, cy - 14,
            fill='#1a1a2e', outline='', tags='sprite'
        )
        ids['mouth'] = self.canvas.create_line(
            cx - 4, cy - 7, cx, cy - 5, cx + 4, cy - 7,
            fill='#c0392b', width=2, smooth=True, tags='sprite'
        )
        
        ids['arm_l'] = self.canvas.create_line(
            cx - 10, cy + 5, cx - 22, cy + 22,
            fill='#3498db', width=6, capstyle='round', tags='sprite'
        )
        ids['arm_r'] = self.canvas.create_line(
            cx + 10, cy + 5, cx + 22, cy + 22,
            fill='#3498db', width=6, capstyle='round', tags='sprite'
        )
        
        ids['leg_l'] = self.canvas.create_rectangle(
            cx - 9, cy + 35, cx - 1, cy + 58,
            fill='#2c3e50', outline='', tags='sprite'
        )
        ids['leg_r'] = self.canvas.create_rectangle(
            cx + 1, cy + 35, cx + 9, cy + 58,
            fill='#2c3e50', outline='', tags='sprite'
        )
        self.player.ids = ids

    def _update_sprites(self):
        p = self.player
        cx, cy = self._world_to_screen(p.wx + Player.W, p.wy)
        ids = p.ids

        
        ex = 2 * p.face_dir

        sw = math.sin(p.arm_swing)
        leg_sw = math.sin(p.arm_swing * 1.1)

        self.canvas.coords(ids['body'],
            cx - 10, cy,       cx + 10, cy + 35)
        self.canvas.coords(ids['head'],
            cx - 12, cy - 25,  cx + 12, cy)
        self.canvas.coords(ids['eye_l'],
            cx - 8 + ex, cy - 19, cx - 3 + ex, cy - 13)
        self.canvas.coords(ids['eye_r'],
            cx + 3 + ex, cy - 19, cx + 8 + ex, cy - 13)
        self.canvas.coords(ids['pupil_l'],
            cx - 7 + ex, cy - 18, cx - 4 + ex, cy - 14)
        self.canvas.coords(ids['pupil_r'],
            cx + 4 + ex, cy - 18, cx + 7 + ex, cy - 14)
        self.canvas.coords(ids['mouth'],
            cx - 4, cy - 7,  cx, cy - 5,  cx + 4, cy - 7)

        al = sw * 10
        ar = -sw * 10
        self.canvas.coords(ids['arm_l'],
            cx - 10, cy + 5,  cx - 22, cy + 22 + al)
        self.canvas.coords(ids['arm_r'],
            cx + 10, cy + 5,  cx + 22, cy + 22 + ar)

        ll = leg_sw * 8
        lr = -leg_sw * 8
        self.canvas.coords(ids['leg_l'],
            cx - 9,  cy + 35 + ll, cx - 1, cy + 58 + ll)
        self.canvas.coords(ids['leg_r'],
            cx + 1,  cy + 35 + lr, cx + 9, cy + 58 + lr)


    def _world_to_screen(self, wx, wy):
        return wx - self.cam_x, wy - self.cam_y

    def _screen_to_world(self, sx, sy):
        return sx + self.cam_x, sy + self.cam_y

    def _screen_to_tile(self, sx, sy):
        wx, wy = self._screen_to_world(sx, sy)
        return int(wx // World.GRID), int(wy // World.GRID)

    
    def _update_camera(self):
        p = self.player
        pcx, pcy = p.wx + Player.W, p.wy + Player.H / 2
        self.tcam_x = pcx - self.SCREEN_W / 2
        self.tcam_y = pcy - self.SCREEN_H / 2

        self.cam_x = lerp(self.cam_x, self.tcam_x, self.CAM_LERP)
        self.cam_y = lerp(self.cam_y, self.tcam_y, self.CAM_LERP)

    

    def _update_blocks(self):
        G   = World.GRID
        pad = self.VP_PAD
        c0  = max(0, int(self.cam_x // G) - pad)
        c1  = min(self.world.COLS - 1, int((self.cam_x + self.SCREEN_W) // G) + pad)
        r0  = max(0, int(self.cam_y // G) - pad)
        r1  = min(self.world.ROWS - 1, int((self.cam_y + self.SCREEN_H) // G) + pad)

        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                cell = self.world.grid[r][c]
                sx = c * G - self.cam_x
                sy = r * G - self.cam_y
                self.canvas.coords(cell['id'], sx, sy, sx + G, sy + G)

        
        if self.tick_count % 10 == 0:
            for r in range(self.world.ROWS):
                for c in range(self.world.COLS):
                    if r < r0 or r > r1 or c < c0 or c > c1:
                        self.canvas.coords(self.world.grid[r][c]['id'],
                                           -100, -100, -100, -100)

    

    def _update_sky(self):
        
        t = self.tick_count % self.DAY_TICKS
        phase = t / self.DAY_TICKS          

        if phase < 0.45:                    
            self.day_factor = 1.0
        elif phase < 0.5:                   
            self.day_factor = 1.0 - (phase - 0.45) / 0.05
        elif phase < 0.9:                   
            self.day_factor = 0.0
        else:                               
            self.day_factor = (phase - 0.9) / 0.1

        df = self.day_factor

        
        for i, bid in enumerate(self.sky_bands):
            t_band = i / len(self.sky_bands)
            if df > 0.5:                    
                top_c    = lerp_color('#4fa3d1', '#c8e6f5', df)
                bottom_c = lerp_color('#87ceeb', '#e0f4ff', df)
            else:                           
                top_c    = lerp_color('#0d1b2a', '#4fa3d1', df * 2)
                bottom_c = lerp_color('#1a3050', '#87ceeb', df * 2)

            if 0.45 < phase < 0.55 or 0.85 < phase < 1.0:  
                dawn_mix = 1 - abs(phase - 0.5) / 0.05 if phase < 0.55 \
                           else (phase - 0.85) / 0.15
                dawn_mix = clamp(dawn_mix, 0, 1) * 0.5
                top_c    = lerp_color(top_c,    SKY_DAWN, dawn_mix * (1 - t_band))
                bottom_c = lerp_color(bottom_c, SKY_DAWN, dawn_mix * t_band)

            band_color = lerp_color(top_c, bottom_c, t_band)
            self.canvas.itemconfig(bid, fill=band_color)

        
        sun_angle  = phase * math.tau - math.pi / 2
        moon_angle = sun_angle + math.pi
        r_orbit    = 260
        ox, oy     = self.SCREEN_W / 2, self.SCREEN_H * 0.55

        sx = ox + math.cos(sun_angle)  * r_orbit - 30
        sy = oy + math.sin(sun_angle)  * r_orbit - 30
        self.canvas.coords(self.sun_id, sx, sy, sx + 60, sy + 60)
        sun_vis = '#f1c40f' if df > 0.05 else ''
        self.canvas.itemconfig(self.sun_id, fill=sun_vis)

        mx = ox + math.cos(moon_angle) * r_orbit - 25
        my = oy + math.sin(moon_angle) * r_orbit - 25
        self.canvas.coords(self.moon_id, mx, my, mx + 50, my + 50)
        moon_vis = '#dcdde1' if df < 0.95 else ''
        self.canvas.itemconfig(self.moon_id, fill=moon_vis)

        
        for cloud in self.clouds:
            cloud['wx'] -= 0.3
            if cloud['wx'] < self.cam_x - 300:
                cloud['wx'] = self.cam_x + self.SCREEN_W + 200
            sx = cloud['wx'] - self.cam_x * 0.15
            sy = cloud['wy'] - self.cam_y * 0.05
            x0, y0, x1, y1 = self.canvas.bbox(cloud['id'])
            w, h = x1 - x0, y1 - y0
            self.canvas.coords(cloud['id'], sx, sy, sx + w, sy + h)
            alpha = int(200 * df)
            grey  = 255 - int(50 * (1 - df))
            self.canvas.itemconfig(cloud['id'],
                                   fill=rgb_to_hex(grey, grey, grey))

    
    def _recolor_blocks(self):
        """Called every 15 ticks – recolour visible blocks for day/night."""
        G   = World.GRID
        c0  = max(0, int(self.cam_x // G) - 1)
        c1  = min(self.world.COLS - 1, int((self.cam_x + self.SCREEN_W) // G) + 1)
        r0  = max(0, int(self.cam_y // G) - 1)
        r1  = min(self.world.ROWS - 1, int((self.cam_y + self.SCREEN_H) // G) + 1)

        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                cell = self.world.grid[r][c]
                bt   = cell['type']
                if bt == 'air':
                    continue
                color = self.world._block_color(bt, r, self.day_factor)
                self.canvas.itemconfig(cell['id'], fill=color)

    

    def _spawn_particles(self, wx, wy, color, count=12):
        sx, sy = self._world_to_screen(wx, wy)
        for _ in range(count):
            p = Particle(sx, sy, color, self.canvas)
            self.particles.append(p)

    def _update_particles(self):
        alive = []
        for p in self.particles:
            if p.update(self.canvas):
                alive.append(p)
            else:
                self.canvas.delete(p.canvas_id)
        self.particles = alive

    

    def _notify(self, text):
        y_off = 20 + len(self.notifications) * 50
        r_id = self.canvas.create_rectangle(
            self.SCREEN_W - 290, y_off,
            self.SCREEN_W - 10,  y_off + 40,
            fill='#45a29e', outline='white', width=2, tags='notif'
        )
        t_id = self.canvas.create_text(
            self.SCREEN_W - 150, y_off + 20,
            text=text, fill='white', font=('Consolas', 10, 'bold'), tags='notif'
        )
        self.notifications.append({'ids': [r_id, t_id], 'timer': 90})

    def _update_notifications(self):
        active = []
        for n in self.notifications:
            n['timer'] -= 1
            if n['timer'] <= 0:
                for i in n['ids']:
                    self.canvas.delete(i)
            else:
                active.append(n)
        self.notifications = active

    

    def _key_down(self, e):
        self.keys[e.keysym.lower()] = True
        k = e.keysym
        if k in ('1', '2', '3', '4'):
            self.player.selected = int(k) - 1
            self._update_hud()

    def _key_up(self, e):
        self.keys[e.keysym.lower()] = False

    

    def _on_break(self, e):
        c, r = self._screen_to_tile(e.x, e.y)
        bt = self.world.get(c, r)
        if bt in ('air', 'bedrock'):
            return
        
        wx = c * World.GRID + World.GRID / 2
        wy = r * World.GRID + World.GRID / 2
        block_color = BLOCK_DEF[bt][0]
        self._spawn_particles(wx, wy, block_color, count=14)

        self.player.add_item(bt)
        self.world.set_block(c, r, 'air', self.day_factor)
        self._notify(f'+1  {bt.upper()}')
        self._update_hud()

    def _on_place(self, e):
        c, r = self._screen_to_tile(e.x, e.y)
        p = self.player
        if not p.can_place():
            return
        if self.world.get(c, r) != 'air':
            return
        
        pcx = int((p.wx + Player.W) // World.GRID)
        pcy_top = int(p.wy // World.GRID)
        pcy_bot = int((p.wy + Player.H - 1) // World.GRID)
        if c == pcx and pcy_top <= r <= pcy_bot:
            return

        item = p.selected_item()
        p.consume_item()
        self.world.set_block(c, r, item, self.day_factor)
        self._update_hud()

    

    def _craft(self):
        inv = self.player.inventory
        if inv.get('wood', 0) >= 1:
            inv['wood']   -= 1
            inv['planks']  = inv.get('planks', 0) + 4
            self._notify('CRAFTED: 4 x PLANKS')
            self._update_hud()
        else:
            self._notify('Need wood to craft!')

    

    def _update_hud(self):
        sc = self.stat_canvas
        p  = self.player
        sc.delete('all')

        
        sc.create_text(10, 12, text='❤  HP', anchor='w',
                       fill='#ff4d4d', font=('Consolas', 10, 'bold'))
        sc.create_rectangle(10, 26, 210, 40, fill='#1a1a1a')
        hw = max(0, int(p.hp / p.max_hp * 200))
        sc.create_rectangle(10, 26, 10 + hw, 40, fill='#e74c3c')
        sc.create_text(215, 33, text=f'{int(p.hp)}', anchor='w',
                       fill='#e74c3c', font=('Consolas', 9))

        
        sc.create_text(10, 52, text='🍖  Hunger', anchor='w',
                       fill='#ffa333', font=('Consolas', 10, 'bold'))
        sc.create_rectangle(10, 66, 210, 80, fill='#1a1a1a')
        hgw = max(0, int(p.hunger / p.max_hunger * 200))
        sc.create_rectangle(10, 66, 10 + hgw, 80, fill='#e67e22')
        sc.create_text(215, 73, text=f'{int(p.hunger)}', anchor='w',
                       fill='#e67e22', font=('Consolas', 9))

        
        phase = (self.tick_count % self.DAY_TICKS) / self.DAY_TICKS
        tod   = 'DAY' if self.day_factor > 0.6 else ('NIGHT' if self.day_factor < 0.3 else 'DUSK/DAWN')
        sc.create_text(10, 100, text=f'☀  {tod}', anchor='w',
                       fill='#f1c40f', font=('Consolas', 9))

        
        inv = p.inventory
        for i, lbl in enumerate(self.slot_labels):
            item  = p.hotbar[i]
            count = inv.get(item, 0)
            sel   = (i == p.selected)
            lbl.config(
                bg='#45a29e' if sel else '#0b0c10',
                fg='#ffffff'  if sel else '#66fcf1',
                highlightbackground='#66fcf1' if sel else '#45a29e',
                text=f'[{i+1}] {item.upper()}\n  ×{count}'
            )

    

    def _loop(self):
        self.tick_count += 1

        
        self.player.update(self.keys, self.world)


        if self.player.hp <= 0:
            messagebox.showinfo('TCraft', 'Game Over!\nYou died of hunger.')
            self.window.destroy()
            return

        
        self._update_camera()

        
        self._update_sky()
        if self.tick_count % 15 == 0:
            self._recolor_blocks()

        
        self._update_blocks()

       
        self._update_sprites()

        
        self._update_particles()

        
        self.canvas.tag_raise('block')
        self.canvas.tag_raise('sprite')
        self.canvas.tag_raise('particle')
        self.canvas.tag_raise('notif')

        
        self._update_notifications()

        
        if self.tick_count % 3 == 0:
            self._update_hud()

        self.window.after(self.TICK_MS, self._loop)



if __name__ == '__main__':
    root = tk.Tk()
    engine = GameEngine(root)
    root.mainloop()