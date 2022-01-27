# This file is executed on every boot (including wake-boot from deepsleep)
import network

sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

sta_if.active(False)
ap_if.active(False)
