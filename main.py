'''
    This is the main micropiton module for the LILYGO®TTGO T-Wristband smart
        bracelet with the ESP32 controller.
    My version of the bracelet with a 9-Axis MPU9250 gyroscope, with an enlarged
        battery and without a vibration motor.
        
        # C driver st7789 compiled in firmware.
        LCD st7789 (SPI)-> MISO:NULL, MOSI:19, SCLK:18, SC:5, DC:23, RST:26, BL:27
        
        # mpu9250.py, mpu6500.py, ak8963.py frozen in firmware.
        9-Axis MPU9250 (I2C)-> SDA:21, SCL:22, Interrupt:38  
        
        RTC PCF8563 (I2C)-> Interrupt:34  # pcf8563.py frozen too.
        
        Touchpad:33, LED:4, VBUS_ADC:36, TouchPower:25, Battery_ADC:35
        
    https://github.com/chicory-ru/t-wristband
'''

from machine import I2C, Pin, SPI , ADC, deepsleep
import st7789
import time
import pcf8563
import vga2_bold_16x32
import vga2_8x16
import esp32
import mpu9250
import ak8963
from calib import offset, scale

def currentime():
    global touch
    c, flag = 0, 0
    while c < 60:  # Show time 60 second.
        gyro = sensor.acceleration
        if touch < 1:
            if gyro[0] < -0.1 and abs(gyro[0]) > abs(gyro[1]):
                if flag == 3:
                    currentime_horizontal(c)
                else:
                    flag = 3
                    display.rotation(flag)
                    display.fill(st7789.BLACK)
                    static_graphics_horizontal()
                    currentime_horizontal(c)
                    continue
            elif gyro[0] > 0.1 and abs(gyro[0]) > abs(gyro[1]):
                if flag == 1:
                    currentime_horizontal(c)
                else:
                    flag = 1
                    display.rotation(flag)
                    display.fill(st7789.BLACK)
                    static_graphics_horizontal()
                    currentime_horizontal(c)
                    continue
            elif gyro[1] > 0.1 and abs(gyro[0]) < abs(gyro[1]):
                if flag == 2:
                    currentime_vertical(c)
                else:
                    flag = 2
                    display.rotation(flag)
                    display.fill(st7789.BLACK)
                    static_graphics_vertical()
                    currentime_vertical(c)
                    continue
            elif gyro[1] < -0.1 and abs(gyro[0]) < abs(gyro[1]):
                if flag == 0:
                    static_graphics_vertical()
                    currentime_vertical(c)
                else:
                    flag = 0
                    display.rotation(flag)
                    display.fill(st7789.BLACK)
                    static_graphics_vertical()
                    currentime_vertical(c)
                    continue
                
        touch += touchpad.value()
        if touch > 1 and touch < 5:
            if touch == 2:
                display.fill(st7789.BLACK)
            display.text(vga2_bold_16x32, 'Date', 6, 25, 0xF81F)
            time.sleep(1)
            continue
        if touch > 4:
            if touch == 5:
                display.fill(st7789.BLACK)
            display.text(vga2_bold_16x32, 'Menu', 6, 25, 0xF81F)
            time.sleep(1)
            continue
        c += 1
        time.sleep(0.96)

def currentime_horizontal(c):
    display.text(vga2_8x16, f'{r.seconds():0>2}', 129, 20, st7789.YELLOW)
    display.text(vga2_bold_16x32, f'{r.hours():0>2}:{r.minutes():0>2}', 20, 10)
    x1, x2 = 142, 130
    if c & 1:
        x1, x2 = x2, x1
    display.line(136, 41, x1, 60, st7789.BLACK)             
    display.fill_circle(x1, 60, 3, st7789.BLACK)
    display.line(136, 41, x2, 60, st7789.GREEN)            
    display.fill_circle(x2, 60, 3, st7789.GREEN) 
    draw_battery()
      
def currentime_vertical(c):
    display.text(vga2_8x16,  f'{r.seconds():0>2}', 50, 70, st7789.YELLOW)
    display.text(vga2_bold_16x32, f'{r.hours():0>2}:', 0, 17)
    display.text(vga2_bold_16x32, f'{r.minutes():0>2}', 47, 17)
    x1, x2 = 50, 64
    if c & 1:
        x1, x2 = x2, x1
    display.line(57, 92, x1, 130, st7789.BLACK)             
    display.fill_circle(x1, 130, 3, st7789.BLACK)
    display.line(57, 92, x2, 130, st7789.GREEN)
    display.fill_circle(x2, 130, 3, st7789.GREEN)
    draw_battery(horizontal=False)

def static_graphics_vertical():
    display.circle(57, 77, 15, st7789.GREEN)
    display.rect(10, 60, 18, 92, st7789.GREEN)
    display.rect(15, 56, 8, 5, st7789.GREEN)
    display.hline(16, 60, 6, st7789.BLACK)

def static_graphics_horizontal():
    display.circle(136, 26, 15, st7789.GREEN)
    display.rect(14, 48, 92, 18, st7789.GREEN)
    display.rect(105, 53, 5, 8, st7789.GREEN)
    display.vline(105, 54, 6, st7789.BLACK)

def _battery_slider_horizontal(color, volt):
    temp = volt if volt <= 87 else 87
    display.fill_rect(17, 51, temp, 12, color)
    display.fill_rect(17 + temp, 51, 87 - temp, 12, st7789.BLACK)
    
def _battery_slider_vertical(color, volt):
    temp = volt if volt <= 87 else 87
    display.fill_rect(13, 62, 12, 87, color)
    display.fill_rect(13, 62, 12, 87 - (volt if volt <= 87 else 87), st7789.BLACK)
     
def draw_battery(horizontal=True):
    if horizontal:
        slider = _battery_slider_horizontal
    else:
        slider = _battery_slider_vertical   
    volt = battery.read_uv() // 1000
    if 1800 < volt <= 2300:
        slider(st7789.GREEN, (volt-1400)//7) 
    elif 1600 < volt <= 1800:
        slider(st7789.YELLOW, (volt-1400)//7)
    elif 1400 < volt <= 1600:
        slider(st7789.RED, (volt-1400)//7)
    else:
        sleep()

weekday = ('Sunday   ', 'Monday   ', 'Tuesday  ', 'Wednesday', 'Thursday ',
           'Friday   ', 'Saturday ')

def calendar():
    horizontal_rotation()
    day_ = r.day()
    if day_ == 6 or day_ == 0:
        color = st7789.RED
    else:
        color = st7789.GREEN
    display.fill(st7789.BLACK)
    display.text(vga2_bold_16x32, f'{r.date():0>2}.{r.month():0>2}.20{r.year():0>2}', 0, 10)
    display.text(vga2_bold_16x32, weekday[day_], 6, 44, color)
    
    tim = time.time()
    while touchpad.value() == 0:
        if time.time()-tim > 20:
            break
    display.fill(st7789.BLACK)
    sleep()

def horizontal_rotation():
    if sensor.acceleration[0] > 0:
        display.rotation(1)
    else:
        display.rotation(3)

def time_set():
    display.fill(st7789.BLACK)
    time_ = [0, 0]
    color1 = st7789.RED
    color2 = st7789.GREEN
    
    def _set_time_print():
        display.text(vga2_bold_16x32, f'{time_[0]:0>2}', 35, 25, color1)
        display.text(vga2_bold_16x32, ':', 65, 25, st7789.GREEN)
        display.text(vga2_bold_16x32, f'{time_[1]:0>2}', 80, 25, color2)
        
    _set_time_print()
    point, flag = -1, 0
    tim = time.time()
    while time.time()-tim < 50:
        if flag == 0:
            step = steps(23, point)
            point = step[1]
            if step[0] == 1:
                flag = 1
                point = -1
                color2, color1 = color1, color2
            time_[0] = step[1]
        else:
            step = steps(59, point)
            point = step[1]
            if step[0] == 1:
                flag = 2
                break
            time_[1] = step[1]     
        _set_time_print()   
    display.fill(st7789.BLACK)
    if flag == 2:
        r.write_all(seconds=0, minutes=time_[1], hours=time_[0])
        print_saved()
 
def date_set():
    display.fill(st7789.BLACK)
    date_ = [0, 0, 0, 0]
    color1 = st7789.RED
    color2 = st7789.GREEN
    color3 = st7789.GREEN
    
    def _set_date_print():
        display.text(vga2_bold_16x32, f'{date_[0]:0>2}', 0, 25, color1)
        display.text(vga2_bold_16x32, '.', 32, 25, st7789.GREEN)
        display.text(vga2_bold_16x32, f'{date_[1]:0>2}', 47, 25, color2)
        display.text(vga2_bold_16x32, '.20', 78, 25, st7789.GREEN)
        display.text(vga2_bold_16x32, f'{date_[2]:0>2}', 126, 25, color3)
    
    _set_date_print()
    point, flag = -1, 0
    tim = time.time()

    while time.time()-tim < 50:
        if flag == 0:
            step = steps(31, point)
            point = step[1]
            if step[0] == 1:
                flag = 1
                point = -1
                color2, color1 = color1, color2
            date_[0] = step[1]
        elif flag == 1:
            step = steps(12, point)
            point = step[1]
            if step[0] == 1:
                flag = 2
                point = 19
                color2, color3 = color3, color2
            date_[1] = step[1]
        else:
            step = steps(99, point)
            point = step[1]
            if step[0] == 1:
                flag = 3
                point = -1
                break
            date_[2] = step[1]
        _set_date_print()
    display.fill(st7789.BLACK)
    display.text(vga2_bold_16x32, weekday[0], 5, 25, st7789.RED)
    
    tim = time.time()
    while time.time()-tim < 50:
        if flag == 4:
            r.write_all(date=date_[0], month=date_[1], year=date_[2], day=date_[3])
            print_saved()
            break
        if flag == 3:
            step = steps(6, point)
            point = step[1]
            if step[0] == 1:
                flag = 4
            date_[3] = step[1]
        if date_[3] == 6 or date_[3] == 0:
            display.text(vga2_bold_16x32, weekday[date_[3]], 5, 25, st7789.RED)
        else:
            display.text(vga2_bold_16x32, weekday[date_[3]], 5, 25, st7789.GREEN)   

def print_saved():
    display.fill(st7789.BLACK)
    horizontal_rotation()
    display.text(vga2_bold_16x32, 'Saved', 10, 25, st7789.GREEN)
    led.on()
    time.sleep(2)
    led.off()
 
def compass():
    from math import cos, sin, atan2
    
    dfirst = 0
    CX = const(40)
    CY = const(80)
    pi180 = 0.01745329252
    angle_mem = 0
    
    display.fill(st7789.BLACK)
    display.rotation(2)
    display.fill_circle(CX, CY, 3, st7789.GREEN)
    display.fill_circle(CX, 36, 3, st7789.GREEN)
    display.fill_circle(CX, 124, 3, st7789.GREEN)
    
    tim = time.time()
    while time.time()-tim < 149: # The duration of the compass.
        if time.time()-tim > 6:
            if touchpad.value() == 1:
                display.fill(st7789.BLACK)
                horizontal_rotation()
                return
            
        xm, ym, zm = sensor.magnetic
        xa, ya, za = sensor.acceleration
        pitch = atan2(ya, (xa*xa + za*za)**0.5)
        roll = atan2(-xa, (ya*ya + za*za)**0.5)
        x = xm*cos(pitch) + ym*sin(roll)*sin(pitch) - zm*cos(roll)*sin(pitch)
        y = ym*cos(roll) + zm*sin(roll)
        az = int(90 - atan2(y, x)*57.3)
        
        if az < 0:
            az += 360
        if az > 360:
            az -= 360
  
        if dfirst > az:
            if az < 90 and dfirst > 270:
                c = 1
            else:
                c = -1
        else:
            if az > 270 and dfirst < 90:
                c = -1
            else:
                c = 1
            
        if dfirst >= 361:
            dfirst = 1
        if dfirst <= -1:
            dfirst = 359

        angle = dfirst * pi180
        display.rotation(4)
        
        if c < 0:
            display.line(int(CX + cos(angle) * 34),
                         int(CY + sin(angle) * 34),
                         int(CX - cos(angle_mem + 1.5) * 10),
                         int(CY - sin(angle_mem + 1.5) * 10), st7789.RED)
            display.line(int(CX + cos(angle_mem) * 35),
                         int(CY + sin(angle_mem) * 35),
                         int(CX + cos(angle_mem + 1.5) * 10),
                         int(CY + sin(angle_mem + 1.5) * 10), st7789.BLACK)
            display.line(int(CX + cos(angle_mem) * 36),
                         int(CY + sin(angle_mem) * 36),
                         int(CX + cos(angle_mem + 1.5) * 10),
                         int(CY + sin(angle_mem + 1.5) * 10), st7789.BLACK)
        else:
            display.line(int(CX + cos(angle) * 34),
                         int(CY + sin(angle) * 34),
                         int(CX + cos(angle_mem + 1.5) * 10),
                         int(CY + sin(angle_mem + 1.5) * 10), st7789.RED)
            display.line(int(CX + cos(angle_mem) * 35),
                         int(CY + sin(angle_mem) * 35),
                         int(CX - cos(angle_mem + 1.5) * 10),
                         int(CY - sin(angle_mem + 1.5) * 10), st7789.BLACK)
            display.line(int(CX + cos(angle_mem) * 36),
                         int(CY + sin(angle_mem) * 36),
                         int(CX - cos(angle_mem + 1.5) * 10),
                         int(CY - sin(angle_mem + 1.5) * 10), st7789.BLACK)
        if az < 23:
            azt = 'E'
            azt2 = 'W'
        elif az < 68:
            azt = 'NE'
            azt2 = 'SW'
        elif az < 113:
            azt = 'N'
            azt2 = 'S'
        elif az < 158:
            azt = 'NW'
            azt2 = 'SE'
        elif az < 203:
            azt = 'W'
            azt2 = 'E'
        elif az < 248:
            azt = 'SW'
            azt2 = 'NE'
        elif az < 293:
            azt = 'S'
            azt2 = 'N'
        elif az < 338:
            azt = 'SE'
            azt2 = 'NW'
        elif az < 361:
            azt = 'E'
            azt2 = 'W'

        display.text(vga2_bold_16x32, f' {azt2} ', 10, 0)
        display.rotation(2)
        display.text(vga2_bold_16x32, f' {azt} ', 10, 0)
        angle_mem = angle
        dfirst += c
    display.fill(st7789.BLACK)

def calibrate():
    display.fill(st7789.BLACK)
    display.text(vga2_bold_16x32, 'Rotate   ', 10, 25, st7789.GREEN)
    offset, scale = sensor.ak8963.calibrate(count=256, delay=200)
    
    with open('calib.py', 'w') as text:
        text.write(f'offset = {offset}\nscale = {scale}')
    print_saved()

def wifipoints():
    import boot
    display.fill(st7789.BLACK)
    display.text(vga2_bold_16x32, 'Scanning', 10, 25, st7789.GREEN)
    boot.sta_if.active(True)
    scanlist = sta_if.scan()
    boot.sta_if.active(False)
    display.fill(st7789.BLACK)
    point = 0
    tim = time.time()
    while time.time()-tim < 100:
        step = steps(len(scanlist), point)
        point = step[1] if point < len(scanlist)-6 else 0
        if step[0] == 1:
            break
        for i in range(5):
            display.text(vga2_8x16, f'{scanlist[step[1]+i][0]:s} {scanlist[step[1]+i][3]}{' '*15}',
                         10, 16*i, st7789.WHITE)
    display.fill(st7789.BLACK)
    time.sleep(1)
    
def game():
    display.fill(st7789.BLACK)
    display.text(vga2_bold_16x32, 'WIP', 45, 25, st7789.GREEN)   
    time.sleep(4)

def menu():
    horizontal_rotation()
    display.fill(st7789.BLACK)
    menutext = 'Exit     ', 'Time set ', 'Date set ', 'Compass  ', 'Calibrate', 'WiFi scan ', 'Game     '
    foo = sleep, time_set, date_set, compass, calibrate, wifipoints, game
    
    point = 0
    tim = time.time()
    while time.time()-tim < 100:
        step = steps(6, point)
        point = step[1]
        if step[0] == 1:
            foo[step[1]]()
            continue
        display.text(vga2_8x16, 'menu', 0, 0, 0xF81F)
        display.text(vga2_bold_16x32, menutext[step[1]], 10, 25, st7789.GREEN)
    sleep()
    
def steps(qty, step=0):         # Counting steps and control of press duration.
    tim = time.time()
    if touchpad.value() != 0:
        while True:
            if touchpad.value() == 0:
                step += 1
                break
            if touchpad.value() == 1 and  time.time()-tim > 2:
                return 1, step
    if step > qty:
        step = 0
    return 0, step   

def sleep(ghost=None):
    global touch
    if touch > 4:
        touch = 0
        menu()
    elif touch > 1:
        touch = 0
        calendar()
    else:
        display.off()
        # Sleep mode is not implemented in the driver, so we use brute force.  
        i2c.writeto_mem(0x69, 0x6B, b'\x40')
        display.sleep_mode(True)
        esp32.wake_on_ext0(pin=touchpad, level=esp32.WAKEUP_ANY_HIGH)
        led.off()
        #print('...Zzz...')
        esp32.gpio_deep_sleep_hold(True)
        time.sleep(0.5)
        deepsleep()

spi = SPI(2, sck=Pin(18), mosi=Pin(19), miso=Pin(23), baudrate=20000000,
          polarity=0, phase=0)

display = st7789.ST7789(spi, 80, 160, cs=Pin(5, Pin.OUT), dc=Pin(23, Pin.OUT),
                        reset=Pin(26, Pin.OUT), backlight=Pin(27, Pin.OUT),
                        color_order=st7789.BGR,
                        rotation=0,
                        options=0,
                        buffer_size=0 )

display.init()

i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)
i2c.writeto_mem(0x69, 0x6B, b'\x00')  # Waking up the gyroscope

r = pcf8563.PCF8563(i2c)

dummy = mpu9250.MPU9250(i2c)
ak8963 = ak8963.AK8963(i2c, offset=offset, scale=scale)
sensor = mpu9250.MPU9250(i2c, ak8963=ak8963)
battery = ADC(Pin(35, Pin.IN), atten=ADC.ATTN_11DB)
touchpad = Pin(33, Pin.IN)
touchpower = Pin(25, Pin.OUT, value=1, hold=True)
led = Pin(4, Pin.OUT)
touch = 0
touchpad.irq(trigger=Pin.IRQ_FALLING, handler=sleep)
currentime()
sleep()


