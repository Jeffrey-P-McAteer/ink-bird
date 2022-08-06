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

bluepy = import_maybe_installing_with_pip('bluepy')

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

def read_temp(dev, characteristic):
  try:
    readings = dev.readCharacteristic(characteristic)
    return float_value(readings[0:2])
  except:
    traceback.print_exc()
    return None



if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal_handler)

  dev_addr = '49:42:07:00:14:3c' # from engbird app

  print(f'Querying {dev_addr}')

  dev = bluepy.btle.Peripheral(dev_addr, addrType=bluepy.btle.ADDR_TYPE_PUBLIC)
  
  while not exit_flag:
    temp_c = read_temp(dev, 0x24)
    
    if temp_c is None:
      dev = bluepy.btle.Peripheral(dev_addr, addrType=bluepy.btle.ADDR_TYPE_PUBLIC)
      print('No temp reading!')
      time.sleep(2)
      continue

    print(f'temp is {temp_c}c, {c_to_f(temp_c)}f')

    time.sleep(2)


  sys.exit(0)

  #for characteristic in range(0x00, 0xff):
  #for characteristic in range(0x28, 0x29):
  for characteristic in range(0x24, 0x24+1):
    if exit_flag:
      continue
    try:
      #characteristic = 0x28
      readings = dev.readCharacteristic(characteristic)
      
      try:
        temperature_c = float_value(readings[0:2])
      except:
        traceback.print_exc()
        temperature_c = -1.0
      
      print(f'characteristic={hex(characteristic)}')
      print(f'raw readings={readings}')
      print(f'temperature_c={temperature_c}')

      # if temperature_c > 25 and temperature_c < 28: # Used to check phone v python reading
      #   print('!!! ^^ got it?')
      #   time.sleep(5)

    except:
      if 'Invalid handle' in traceback.format_exc():
        continue
      traceback.print_exc()





  #code.InteractiveConsole(locals=globals()).interact()


