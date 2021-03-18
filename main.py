'''
    This is the main micropiton module for the LILYGO®TTGO T-Watch-2020 smart bracelet with the ESP32 controller.
    My version of the bracelet with a 9-Axis MPU9250 gyroscope, with an enlarged battery and without a vibration motor.
        
        LCD ST7735 (SPI)-> MISO:NULL, MOSI:19, SCLK:18, SC:5, DC:23, RST:26, BL:27  # C driver st7735 compiled in firmware.
        9-Axis MPU9250 (I2C)-> SDA:21, SCL:22, Interrupt:38  # mpu9250.py, mpu6500.py, ak8963.py
        RTC PCF8563 (I2C)-> Interrupt:34  # pcf8563.py
        Touchpad:33, LED:4, VBUS_ADC:36, TouchPower:25, Battery_ADC:35
        
    https://github.com/chicory-ru
'''

from machine import SoftI2C, Pin, SPI, ADC, deepsleep, Timer
import st7735
import time
import pcf8563
import vga2_bold_16x32
import vga2_8x16
import esp32
import mpu9250

def currentime():
    global touch
    c, flag = 0, 3
    while c < 60:  # Show time 60 second.
        gyro = sensor.acceleration
        if touch < 1:
            if gyro[0] < -0.1 and abs(gyro[0]) > abs(gyro[1]):
                if flag == 3:
                    if c == 0:
                        static_graphics_horizontal()
                    currentime_horizontal(c)
                else:
                    flag = 3
                    display.rotation(flag)
                    display.fill(st7735.BLACK)
                    static_graphics_horizontal()
                    currentime_horizontal(c)
                    continue
            if gyro[0] > 0.1 and abs(gyro[0]) > abs(gyro[1]):
                if flag == 1:
                    currentime_horizontal(c)
                else:
                    flag = 1
                    display.rotation(flag)
                    display.fill(st7735.BLACK)
                    static_graphics_horizontal()
                    currentime_horizontal(c)
                    continue
            if gyro[1] > 0.1 and abs(gyro[0]) < abs(gyro[1]):
                if flag == 2:
                    currentime_vertical(c)
                else:
                    flag = 2
                    display.rotation(flag)
                    display.fill(st7735.BLACK)
                    static_graphics_vertical()
                    currentime_vertical(c)
                    continue
            if gyro[1] < -0.1 and abs(gyro[0]) < abs(gyro[1]):
                if flag == 4:
                    currentime_vertical(c)
                else:
                    flag = 4
                    display.rotation(flag)
                    display.fill(st7735.BLACK)
                    static_graphics_vertical()
                    currentime_vertical(c)
                    continue
        touch += touchpad.value()
        if touch > 1 and touch < 5:
            if touch == 2:
                display.fill(st7735.BLACK)
            display.text(vga2_bold_16x32, 'Date', 6, 25, st7735.PURPLE)
            time.sleep(1)
            continue
        if touch > 4:
            if touch == 5:
                display.fill(st7735.BLACK)
            display.text(vga2_bold_16x32, 'Menu', 6, 25, st7735.PURPLE)
            time.sleep(1)
            continue
        c += 1
        time.sleep(0.95)

def currentime_horizontal(c):
    display.text(vga2_8x16, '{:0>2}'.format(str(r.seconds())), 129, 20, st7735.YELLOW)
    display.text(vga2_bold_16x32, '{:0>2}'.format (str(r.hours())) + \
                 ':' + '{:0>2}'.format(str(r.minutes())), 20, 10)
    x1, x2 = 142, 130
    if c % 2 == 0:
        x1, x2 = x2, x1
    display.line(136, 41, x1, 60, st7735.BLACK)             
    display.circle(x1, 60, 3, st7735.BLACK, st7735.BLACK)
    display.line(136, 41, x2, 60, st7735.GREEN)            # Defined:  BLACK BLUE RED GREEN CYAN MAGENTA
    display.circle(x2, 60, 3, st7735.GREEN, st7735.GREEN)  # YELLOW WHITE MAROON FOREST NAVY PURPLE GRAY
    draw_battery()
      
def currentime_vertical(c):
    display.text(vga2_8x16, '{:0>2}'.format(str(r.seconds())), 50, 70, st7735.YELLOW)
    display.text(vga2_bold_16x32, '{:0>2}'.format (str(r.hours())) + ':', 0, 17)
    display.text(vga2_bold_16x32, '{:0>2}'.format(str(r.minutes())), 47, 17)
    x1, x2 = 50, 64
    if c % 2 == 0:
        x1, x2 = x2, x1
    display.line(57, 92, x1, 130, st7735.BLACK)             
    display.circle(x1, 130, 3, st7735.BLACK, st7735.BLACK)
    display.line(57, 92, x2, 130, st7735.GREEN)
    display.circle(x2, 130, 3, st7735.GREEN, st7735.GREEN)
    draw_battery(horizontal=False)

def static_graphics_vertical():
    display.circle(57, 77, 15, st7735.GREEN, st7735.BLACK)
    display.rect(10, 60, 18, 92, st7735.GREEN)
    display.rect(15, 56, 8, 5, st7735.GREEN)
    display.hline(16, 60, 6, st7735.BLACK)

def static_graphics_horizontal():
    display.circle(136, 26, 15, st7735.GREEN, st7735.BLACK)
    display.rect(14, 48, 92, 18, st7735.GREEN)
    display.rect(105, 53, 5, 8, st7735.GREEN)
    display.vline(105, 54, 6, st7735.BLACK)

def _battery_slider_horizontal(color, volt):
        display.fill_rect(volt-192, 51, 297-volt, 12, st7735.BLACK)
        display.fill_rect(18, 51, volt-210, 12, color)

def _battery_slider_vertical(color, volt):
        display.fill_rect(13, 61, 12, 297-volt, st7735.BLACK)
        display.fill_rect(13, 86-volt-241, 12, volt-208, color)

def draw_battery(horizontal=True):
    if horizontal:
        slider = _battery_slider_horizontal
    else:
        slider = _battery_slider_vertical
    volt = battery.read()
    if volt > 260 and volt <= 297:
        slider(st7735.GREEN, volt)  
    if volt > 220 and volt <= 260:
        slider(st7735.YELLOW, volt)
    if volt > 210  and volt <= 220:
        slider(st7735.RED, volt)
    if volt > 297:
        slider(st7735.GREEN, 297)
    if volt < 165:
        sleep()

weekday = 'None     ', 'Monday   ', 'Tuesday  ', 'Wednesday', 'Thursday ', 'Friday   ', 'Saturday ', 'Sunday   '

def calendar():
    horizontal_rotation()
    day_ = r.day()
    if day_ > 5:
        color = st7735.RED
    else:
        color = st7735.FOREST
    if day_ == 0:
        r.write_all(day=1)
    display.fill(st7735.BLACK)
    display.text(vga2_bold_16x32, '{:0>2}'.format (str(r.date())) + \
                 '.' + '{:0>2}'.format(str(r.month()) +'.20' + \
                 '{:0>2}'.format(str(r.year()))) , 0, 10)
    display.text(vga2_bold_16x32, weekday[day_], 6, 44, color)
    tim.init(period=100000)
    while touchpad.value() == 0:
        if tim.value() > 20000:
            break
    sleep()

def horizontal_rotation():
    if sensor.acceleration[0] > 0:
        display.rotation(1)
    else:
        display.rotation(3)

def time_set():
    display.fill(st7735.BLACK)
    time_ = [0, 0]
    color1 = st7735.RED
    color2 = st7735.GREEN
    def _set_time_print():
        display.text(vga2_bold_16x32, '{:0>2}'.format(str(time_[0])), 35, 25, color1)
        display.text(vga2_bold_16x32, ':', 65, 25, st7735.GREEN)
        display.text(vga2_bold_16x32, '{:0>2}'.format(str(time_[1])), 80, 25, color2)
    _set_time_print()
    point, flag = -1, 0
    tim.init(period=100000)
    while tim.value() < 50000:
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
    display.fill(st7735.BLACK)
    if flag == 2:
        r.write_all(seconds=0, minutes=time_[1], hours=time_[0])
        print_saved()
 
def date_set():
    display.fill(st7735.BLACK)
    date_ = [0, 0, 0, 0]
    color1 = st7735.RED
    color2 = st7735.GREEN
    color3 = st7735.GREEN
    def _set_date_print():
        display.text(vga2_bold_16x32, '{:0>2}'.format(str(date_[0])), 1, 25, color1)
        display.text(vga2_bold_16x32, '.', 33, 25, st7735.GREEN)
        display.text(vga2_bold_16x32, '{:0>2}'.format(str(date_[1])), 48, 25, color2)
        display.text(vga2_bold_16x32, '.20', 79, 25, st7735.GREEN)
        display.text(vga2_bold_16x32, '{:0>2}'.format(str(date_[2])), 127, 25, color3)
    _set_date_print()
    point, flag = -1, 0
    tim.init(period=100000)
    while tim.value() < 50000:
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
    display.fill(st7735.BLACK)
    display.text(vga2_bold_16x32, weekday[1], 5, 25, st7735.FOREST)
    while tim.value() < 50000:
        if flag == 4:
            r.write_all(date=date_[0], month=date_[1], year=date_[2], day=date_[3])
            print_saved()
            break
        if flag == 3:
            step = steps(6, point)
            point = step[1]
            if step[0] == 1:
                flag = 4
            date_[3] = step[1]+1
        display.text(vga2_bold_16x32, weekday[date_[3]], 5, 25, st7735.FOREST)   

def print_saved():
    display.fill(st7735.BLACK)
    display.text(vga2_bold_16x32, 'Saved', 10, 25, st7735.GREEN)
    led.on()
    time.sleep(2)
    led.off()
    
def compas():
    display.fill(st7735.BLACK)
    display.text(vga2_bold_16x32, 'In work.', 10, 25, st7735.GRAY)   
    time.sleep(4)

def menu():
    horizontal_rotation()
    display.fill(st7735.BLACK)
    menutext = 'Exit    ', 'Time set', 'Date set', 'Compas  ' 
    foo = sleep, time_set, date_set, compas 
    point = 0
    tim.init(period=100000)
    while tim.value() < 50000:
        step = steps(3, point)
        point = step[1]
        if step[0] == 1:
            foo[step[1]]()
            continue
        display.text(vga2_8x16, 'menu', 0, 0, st7735.PURPLE)
        display.text(vga2_bold_16x32, menutext[step[1]], 10, 25, st7735.GREEN)
    sleep()
    
def steps(qty, step=0):         # Counting steps and control of press duration.
    if touchpad.value() != 0:
        tim.init(period=100000)
        while True:
            if touchpad.value() == 0:
                step += 1
                break
            if touchpad.value() == 1 and tim.value() > 2000:
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
        esp32.wake_on_ext0(pin=touchpad, level=esp32.WAKEUP_ANY_HIGH)
        Pin(27, Pin.PULL_HOLD)
        display.sleep_mode(1)
        i2c.writeto_mem(0x69, 0x6B, b'\x40')  # Sleep mode is not implemented in the driver, so we use brute force.
        time.sleep_ms(500)
        tim.deinit()
        led.off()
        print("\n...Zzz...")
        deepsleep()

spi = SPI(2, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(23, Pin.OUT), baudrate=30000000, polarity=0, phase=0)
display = st7735.ST7735(spi, 80, 160, cs=Pin(5, Pin.OUT), dc=Pin(23, Pin.OUT), reset=Pin(26, Pin.OUT), backlight=Pin(27, Pin.OUT), rotation=3)
display.init()

i2c = SoftI2C(scl=Pin(22, Pin.OUT), sda=Pin(21, Pin.OUT))
i2c.writeto_mem(0x69, 0x6B, b'\x00')  # Waking up the gyroscope
#print([hex(i) for i in i2c.scan()])
r = pcf8563.PCF8563(i2c)
#_________________________________________________
sensor = mpu9250.MPU9250(i2c)
# For some reason, the drivers issue accelerometer readings to the gyroscope request and vice versa. 
# I didn't understand. Further to get gyroscope readings I will use sensor.acceleration
#_________________________________________________
battery = ADC(Pin(35, Pin.IN))
battery.width(ADC.WIDTH_9BIT)
battery.atten(ADC.ATTN_11DB)
touchpad = Pin(33, Pin.IN)
touchpower = Pin(25, Pin.OUT, Pin.PULL_HOLD, value=1)
led = Pin(4, Pin.OUT)
touch = 0
tim = Timer(1)
touchpad.irq(trigger=Pin.IRQ_FALLING, handler=sleep)
currentime()
sleep()