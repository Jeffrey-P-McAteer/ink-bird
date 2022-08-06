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
  return float(num) / 100

def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal_handler)
  known_bad_macs = [
    '5f:95:af:d4:62:fd', '0f:a0:69:47:97:9d', '44:17:4d:23:91:2a', '79:51:c5:8e:a6:ec', '78:25:15:a1:b5:6c',
    'cc:9f:f7:4e:c3:92', '75:35:ba:d0:55:7e', '53:d9:94:7a:97:fc', '7f:18:2b:4e:fe:12', 'f3:5f:74:88:7a:b9',
    '7f:b7:bd:f3:46:42',
  ]
  try:
    if os.path.exists('bad_macs.pickle.bin'):
      with open('bad_macs.pickle.bin', 'rb') as fd:
        known_bad_macs.extend(
          pickle.load(fd)
        )
  except:
    traceback.print_exc()

  known_bad_macs = list(set(known_bad_macs))
  print(f'known_bad_macs={known_bad_macs}')

  exit_flag = False
  while not exit_flag:
    try:
      scanner = bluepy.btle.Scanner()
      btle_devices = scanner.scan(timeout=11)
      
      for d in btle_devices:
        if d.addr.lower() in known_bad_macs:
          print(f'Skipping {d.addr} scan data = {d.getScanData()}')
          continue
        try:
          print(f'{d.addr} scan data = {d.getScanData()}')
          print(f'Attempting to read from {d.addr}')
          dev = bluepy.btle.Peripheral(d.addr, addrType=bluepy.btle.ADDR_TYPE_PUBLIC)
          
          for characteristic in range(0x00, 0xff):
            try:
              #characteristic = 0x28
              print(f'characteristic={hex(characteristic)}')
              readings = dev.readCharacteristic(characteristic)
              print(f'raw readings={readings}')

              temperature_c = float_value(readings[0:2])
              print(f'temperature_c={temperature_c}')
              if temperature_c > 60.0 and temperature_c < 80.0:
                print('')
                print(f'!!! Got a good reading from mac {d.addr}  characteristic={hex(characteristic)}')
                time.sleep(100)
                subprocess.run([
                  'ding', f'!!! Got a good reading from mac {d.addr}  characteristic={hex(characteristic)} temperature_c={temperature_c}'
                ], check=False);
                print('')
            except:
              traceback.print_exc()

        except:
          traceback.print_exc()
          if 'Failed to connect to' in traceback.format_exc():
            known_bad_macs.append( d.addr.lower() )
            #print(f'increased known_bad_macs={known_bad_macs}')
            with open('bad_macs.pickle.bin', 'wb') as fd:
              pickle.dump(known_bad_macs, fd)

        print('')
        print('')
    except:
      traceback.print_exc()

  # print(f'Attempting to read from {sensor_mac}')

  # dev = bluepy.btle.Peripheral(sensor_mac, addrType=bluepy.btle.ADDR_TYPE_PUBLIC)
  # readings = dev.readCharacteristic(0x28)
  # print(f'readings={readings}')




  #code.InteractiveConsole(locals=globals()).interact()


