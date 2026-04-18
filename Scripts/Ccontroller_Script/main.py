import pygame
import serial

# --- CONFIGURATION ---
ESP_PORT = 'COM5' 
BAUD_RATE = 115200

# Gamepad Axis IDs (Enter E-GPV10 Standard)
THROTTLE_AXIS = 1  # Left Stick Up/Down
STEER_AXIS = 2     # Right Stick Left/Right (Try 3 if 2 doesn't work)

# Sensitivity Settings (0.1 to 1.0)
# Lower these if the robot is too fast or hard to control
DRIVE_SENSITIVITY = 0.7  # 0.7 = 70% of max speed
STEER_SENSITIVITY = 0.4  # 0.5 = 50% of max turning speed
DEADZONE = 0.12          # Ignore small stick drifts (12%)

# --- INITIALIZATION ---
pygame.init()
pygame.joystick.init()

screen = pygame.display.set_mode((400, 350)) # Slightly taller for extra info
pygame.display.set_caption("RC Rover - Dual Sensitivity Mode")
font = pygame.font.SysFont("Consolas", 18)

# Serial Connection
try:
    esp32 = serial.Serial(port=ESP_PORT, baudrate=BAUD_RATE, timeout=0.1)
    connected = True
except Exception:
    connected = False
    print(f"ESP32 NOT FOUND on {ESP_PORT}. Running in Offline Mode.")

# Gamepad Connection
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
else:
    print("No gamepad detected!")
    pygame.quit()
    exit()

clock = pygame.time.Clock()
running = True

# --- MAIN LOOP ---
while running:
    screen.fill((30, 30, 35)) # Dark Navy background
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Read Raw Values (-1.0 to 1.0)
    raw_throttle = joystick.get_axis(THROTTLE_AXIS)
    raw_steer = joystick.get_axis(STEER_AXIS)

    # 2. Apply Deadzone
    if abs(raw_throttle) < DEADZONE: raw_throttle = 0
    if abs(raw_steer) < DEADZONE: raw_steer = 0

    # 3. Calculate Motor Values (-255 to 255)
    # -255 inverts the Y-axis so UP is Forward (+)
    drive = int(raw_throttle * 255 * DRIVE_SENSITIVITY)
    
    # Steering Logic with sensitivity
    steer = int(raw_steer * -255 * STEER_SENSITIVITY)

    # 4. Send Data over USB Serial
    if connected:
        command = f"{drive},{steer}\n"
        esp32.write(command.encode('utf-8'))

    # 5. UI DASHBOARD
    # Connection Status
    status_text = "SERIAL: ONLINE" if connected else "SERIAL: OFFLINE"
    status_col = (0, 255, 150) if connected else (255, 50, 50)
    screen.blit(font.render(status_text, True, status_col), (20, 20))
    
    # Sensitivity Displays
    screen.blit(font.render(f"Throttle Sens: {int(DRIVE_SENSITIVITY*100)}%", True, (255, 255, 255)), (20, 60))
    screen.blit(font.render(f"Steering Sens: {int(STEER_SENSITIVITY*100)}%", True, (255, 255, 255)), (20, 90))

    # Throttle Visual Bar
    pygame.draw.rect(screen, (70, 70, 70), (20, 130, 360, 25)) # Background
    t_width = int((drive / 255) * 180)
    pygame.draw.rect(screen, (0, 200, 255), (200, 130, t_width, 25))
    screen.blit(font.render(f"Drive: {drive}", True, (200, 200, 200)), (20, 160))

    # Steering Visual Bar
    pygame.draw.rect(screen, (70, 70, 70), (20, 200, 360, 25)) # Background
    s_width = int((steer / 255) * 180)
    pygame.draw.rect(screen, (255, 200, 0), (200, 200, s_width, 25))
    screen.blit(font.render(f"Steer: {steer}", True, (200, 200, 200)), (20, 230))

    # Footer
    screen.blit(font.render("Press 'Analog' on Pad", True, (100, 100, 100)), (20, 310))

    pygame.display.flip()
    clock.tick(30) 

if connected:
    esp32.close()
pygame.quit()