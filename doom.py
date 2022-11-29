import pygame, math
from pygame.constants import K_LEFT, K_SPACE, K_a, K_d, K_s, K_w, MOUSEMOTION
pygame.init()

WIDTH = 800
HEIGHT = 600
size = (WIDTH, HEIGHT)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Doom")
clock = pygame.time.Clock()
FPS = 60
CELL_SIZE = 50 # must be able to fit into both 800 & 600
CELLS_W = int(size[0] / CELL_SIZE)
CELLS_H = int(size[1] / CELL_SIZE)
MAP_SCALE = .4 # the fraction of the screen that the map takes up
SCALED_WIDTH = WIDTH * MAP_SCALE
SCALED_HEIGHT = HEIGHT * MAP_SCALE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
COLOR_THEME = (BLACK, WHITE, RED)
RESOLUTION = 64
FISHEYE = False
cells = []
walls = [(pygame.Vector2(0, 0), pygame.Vector2(WIDTH, 0)), (pygame.Vector2(0, 0), pygame.Vector2(0, HEIGHT)),
         (pygame.Vector2(WIDTH, 0), pygame.Vector2(WIDTH, HEIGHT)),  (pygame.Vector2(0, HEIGHT), pygame.Vector2(WIDTH, HEIGHT))]

class Cell:    
    def __init__(self, pos, s):
        self.color = COLOR_THEME[0]
        self.pos = pos
        self.size = s
        self.type = "empty"
        self.rect = pygame.draw.rect(screen, self.color, (self.pos.x, self.pos.y, self.size, self.size))
        o = 1 # a small offset to account for corners
        line1 = (pygame.Vector2(self.pos.x-o, self.pos.y), pygame.Vector2(self.pos.x+self.size+o, self.pos.y))
        line2 = (pygame.Vector2(self.pos.x, self.pos.y-o), pygame.Vector2(self.pos.x, self.pos.y+self.size+o))
        line3 = (pygame.Vector2(self.pos.x-0, self.pos.y+self.size), pygame.Vector2(self.pos.x+self.size+o, self.pos.y+self.size))
        line4 = (pygame.Vector2(self.pos.x+self.size, self.pos.y-0), pygame.Vector2(self.pos.x+self.size, self.pos.y+self.size+o))
        # each cell has four walls
        self.walls = [line1, line2, line3, line4]
    
    def draw(self):
        if self.type == "empty":
            self.color = COLOR_THEME[0]
        elif self.type == "wall":
            self.color = COLOR_THEME[1]
        pygame.draw.rect(screen, self.color, (self.pos.x * MAP_SCALE, self.pos.y * MAP_SCALE, self.size * MAP_SCALE, self.size * MAP_SCALE))
        # pygame.draw.rect(screen, COLOR_THEME[1], (self.pos.x, self.pos.y, self.size, self.size), 1) # border

class Player:
    def __init__(self, pos, vdist, theta, FOV, resolution):
        self.pos = pos
        self.theta = theta
        self.vdist = vdist
        self.dir = pygame.Vector2(math.cos(math.radians(self.theta)), math.sin(math.radians(self.theta))).normalize()
        self.dir_ray = self.dir*self.vdist
        self.fov = FOV
        self.vel = 2
        self.angl_vel = 1
        self.resolution = resolution # the number of rays in the fov

    def draw(self):
        pygame.draw.circle(screen, COLOR_THEME[1], self.pos * MAP_SCALE, 5 * MAP_SCALE)
        # draw fov
        for t in range(self.resolution):
            angle = self.theta - (self.fov/2) + t*(self.fov/self.resolution)
            new_dir = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
            new_dir_ray = new_dir * self.vdist
            collide = self.cast(new_dir)
            if collide:
                update_segment(t, (collide - self.pos), self.dir_ray)
                pygame.draw.circle(screen, COLOR_THEME[2], collide * MAP_SCALE, 2)
                pygame.draw.aaline(screen, COLOR_THEME[1], self.pos * MAP_SCALE, collide * MAP_SCALE)
            else:
                # update_segment(t, new_dir_ray, self.dir_ray)
                pygame.draw.aaline(screen, COLOR_THEME[1], self.pos * MAP_SCALE, (self.pos + new_dir_ray) * MAP_SCALE)

    def update(self):
        self.dir = pygame.Vector2(math.cos(math.radians(self.theta)), math.sin(math.radians(self.theta))).normalize()
        self.dir_ray = self.dir * self.vdist

    def cast(self, ray_dir):
        collision_point = None
        collision_dist = float('inf') # the distance of the nearest collision
        for wall in walls:
            if (self.collide(ray_dir, wall)):
                pt = self.collide(ray_dir, wall)
                dist = pygame.math.Vector2.distance_to(self.pos, pt)
                if (dist < collision_dist and dist < self.vdist):
                    collision_dist = dist
                    collision_point = pt
        return collision_point

    def collide(self, ray_dir, line):
        x1 = line[0].x
        y1 = line[0].y
        x2 = line[1].x
        y2 = line[1].y

        x3 = self.pos.x
        y3 = self.pos.y
        x4 = self.pos.x + ray_dir.x
        y4 = self.pos.y + ray_dir.y
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if (den == 0):
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if (t > 0 and t < 1 and u > 0):
            pt = pygame.Vector2(x1 + t * (x2 - x1), y1 + t * (y2 - y1))
            return pt
        return None

    def rotate(self, theta):
        self.theta += theta
        self.dir = pygame.Vector2(math.cos(math.radians(self.theta)), math.sin(math.radians(self.theta))).normalize()
        self.dir_ray = self.dir * self.vdist

    def move(self, dir):
        if (dir == "forward"):
            new_x = self.pos.x + (self.vel * math.cos(math.radians(self.theta)))
            new_y = self.pos.y + (self.vel * math.sin(math.radians(self.theta)))
            self.pos = pygame.Vector2(new_x, new_y)
        else:
            new_x = self.pos.x - (self.vel * math.cos(math.radians(self.theta)))
            new_y = self.pos.y - (self.vel * math.sin(math.radians(self.theta)))
            self.pos = pygame.Vector2(new_x, new_y)

def update_segment(index, ray, dir):
    if FISHEYE:
        projection = ray.length()
    else:
        projection = abs(ray.dot(dir)/dir.length())
    color = map(projection, dir.length(), 0, 0, 255)
    width = size[0] - (size[0]*MAP_SCALE)
    height = map(projection, 0, dir.length(), HEIGHT, 0)
    rect = pygame.Rect((index * round(width/RESOLUTION)) + (size[0]*MAP_SCALE), (HEIGHT - height) / 2, round(width/RESOLUTION), height)
    pygame.draw.rect(screen, (color, color, color), rect)
    pygame.draw.line(screen, COLOR_THEME[2], (size[0]*MAP_SCALE, 0), (size[0]*MAP_SCALE, size[1]))
    

def map(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def toggle_cell(mouse_pos):
    for cell in cells:
        scaled_rect = pygame.Rect(cell.rect.x * MAP_SCALE, cell.rect.y * MAP_SCALE, CELL_SIZE * MAP_SCALE, CELL_SIZE * MAP_SCALE)
        if scaled_rect.collidepoint(mouse_pos):
            if (cell.type == "empty"):
                cell.type = "wall"
                for wall in cell.walls:
                    walls.append(wall)
            elif (cell.type == "wall"):
                cell.type = "empty"
                for wall in cell.walls:
                    walls.remove(wall)
            break

# Draw map
for i in range(CELLS_H):
    for j in range(CELLS_W):
        cell = Cell(pygame.Vector2(j * CELL_SIZE, i * CELL_SIZE), CELL_SIZE)
        cells.append(cell)

player = Player(pygame.Vector2(size[0]/2*MAP_SCALE, size[1]/2*MAP_SCALE), 500, 0, 90, RESOLUTION)

running = True;
while running :
    pygame.display.set_caption("Doom  fps:" + str(int(clock.get_fps())) + " fisheye: " + str(FISHEYE) + " fov: " + str(player.fov) + " vdist: " + str(player.vdist))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            toggle_cell(pygame.mouse.get_pos())
        if event.type == pygame.KEYUP:
            if event.key == K_SPACE:
                FISHEYE = not FISHEYE

    keys = pygame.key.get_pressed()
    if (keys[pygame.K_RIGHT]):
        player.rotate(player.angl_vel)
    if (keys[pygame.K_LEFT]):
        player.rotate(-player.angl_vel)
    if (keys[pygame.K_UP]):
        player.move("forward")
    if (keys[pygame.K_DOWN]):
        player.move("backward")
    if (keys[pygame.K_a]):
        player.fov -= 1
    if (keys[pygame.K_d]):
        player.fov += 1
    if (keys[pygame.K_w]):
        player.vdist += 1
        player.update()
    if (keys[pygame.K_s]):
        player.vdist -= 1
        player.update()
    if (keys[pygame.K_r]):
        RESOLUTION += 1
        player.resolution += 1
    if (keys[pygame.K_e]):
        RESOLUTION -= 1
        player.resolution -= 1
    player.pos.x = player.pos.x % size[0]
    player.pos.y = player.pos.y % size[1]

    screen.fill(BLACK)
    # draw projection


    # draw minimap
    for cell in cells:
        cell.draw()
    player.draw()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
