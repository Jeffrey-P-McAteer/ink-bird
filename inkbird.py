#!/usr/bin/env python

# Python builtins
import os
import sys
import subprocess
import shutil
import importlib
import asyncio
import ssl
import traceback
import json
import random
import time
import io
import base64
import code
import pickle
import signal

# Utility method to wrap imports with a call to pip to install first.
# > "100% idiot-proof!" -- guy on street selling rusty dependency chains.
def import_maybe_installing_with_pip(import_name, pkg_name=None):
  if pkg_name is None:
    pkg_name = import_name # 90% of all python packages share their name with their module
  pkg_spec = importlib.util.find_spec(import_name)
  install_cmd = []
  if pkg_spec is None:
    # package missing, install via pip to user prefix!
    print('Attempting to install module {} (package {}) with pip...'.format(import_name, pkg_name))
    install_cmd = [sys.executable, '-m', 'pip', 'install', '--user', pkg_name]
    subprocess.run(install_cmd, check=False)
  pkg_spec = importlib.util.find_spec(import_name)
  if pkg_spec is None:
    raise Exception('Cannot find module {}, attempted to install {} via pip: {}'.format(import_name, pkg_name, ' '.join(install_cmd) ))
  
  return importlib.import_module(import_name)

# 3rd-party libs
# yay -S python-pybluez (arch linux breaks when using pip for this b/c too new libs)
# bluetooth = import_maybe_installing_with_pip('bluetooth', 'pybluez')

#bluepy = import_maybe_installing_with_pip('bluepy') # Linux only

bleak = import_maybe_installing_with_pip('bleak')

def float_value(nums):
  # check if temp is negative
  num = (nums[1]<<8)|nums[0]
  if nums[1] == 0xff:
      num = -( (num ^ 0xffff ) + 1)
  return round(float(num) / 100.0, 3)

exit_flag = False
def signal_handler(sig, frame):
  global exit_flag
  exit_flag = True
  print('Exiting...')
  sys.exit(0)

def c_to_f(temperature_c):
  return round(9.0/5.0 * temperature_c + 32, 3)

async def read_temp(dev, characteristic):
  try:
    #readings = dev.readCharacteristic(characteristic)
    readings = await dev.read_gatt_char(int(characteristic))
    return float_value(readings[0:2])
  except:
    traceback.print_exc()
    return None

async def main():
  global exit_flag

  dev_addr = '49:42:07:00:14:3c' # from engbird app
  temp_adjustment_deg_c = -2.5 # Sensor cannot be calibrated, is a s/w fix to print calibrated reading.

  print(f'Querying {dev_addr}')

  async with bleak.BleakClient(dev_addr) as dev:
    #dev = bluepy.btle.Peripheral(dev_addr, addrType=bluepy.btle.ADDR_TYPE_PUBLIC)

    
    while not exit_flag:
      if not dev.is_connected:
        print('Calling dev.connect()...')
        await dev.connect()

      #temp_c = await read_temp(dev, 0x24) # Whoops?
      temp_c = await read_temp(dev, 0x23)
      if not temp_c is None:
        temp_c += temp_adjustment_deg_c

      if temp_c is None:
        #dev = bluepy.btle.Peripheral(dev_addr, addrType=bluepy.btle.ADDR_TYPE_PUBLIC)
        try:
          print('Calling dev.disconnect()...')
          await dev.disconnect()
        except:
          traceback.print_exc()

        print('dev = bleak.BleakClient(dev_addr) ...')
        dev = bleak.BleakClient(dev_addr)
        print('No temp reading!')
        time.sleep(2)
        continue

      print(f'temp is {temp_c}c, {c_to_f(temp_c)}f')

      time.sleep(2)


if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal_handler)
  asyncio.run(main())


