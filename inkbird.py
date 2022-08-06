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

# Config
dev_addr = '49:42:07:00:14:3c' # device bluetooth MAC from engbird app
temp_adjustment_deg_c = -2.5   # Sensor cannot be calibrated, app uses a s/w fix to print calibrated reading so we do same
pushover_user_key = os.environ.get('PUSHOVER_USER_KEY', '')
pushover_api_token = os.environ.get('PUSHOVER_API_TOKEN', '')
acceptable_temp_f_bounds = (
  15.0, 42.0 # if temp goes outside bounds, notification is sent
)
min_notification_delay_s = 15 * 60 # If we have already sent a notification in the last 15 minutes, do not send another until 15 minutes has elapsed.
temp_measure_poll_time_s = 4 # check temp every 4 seconds
periodic_report_s = 12 * 60 * 60 # Every 12 hours, send a temp report no matter what


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

bleak = import_maybe_installing_with_pip('bleak')
pushover = import_maybe_installing_with_pip('pushover', 'python-pushover')

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

  pushover_client = pushover.Client(pushover_user_key, api_token=pushover_api_token)
  last_notification_s = 0

  print(f'acceptable_temp_f_bounds = {acceptable_temp_f_bounds}')
  print(f'Querying {dev_addr}')

  async with bleak.BleakClient(dev_addr) as dev:

    while not exit_flag:
      if not dev.is_connected:
        print('Calling dev.connect()...')
        await dev.connect()

      temp_c = await read_temp(dev, 0x23)
      if not temp_c is None:
        temp_c += temp_adjustment_deg_c

      if temp_c is None:
        try:
          print('Calling dev.disconnect()...')
          await dev.disconnect()
        except:
          traceback.print_exc()

        print('dev = bleak.BleakClient(dev_addr) ...')
        dev = bleak.BleakClient(dev_addr)
        print('No temp reading!')
        await asyncio.sleep(temp_measure_poll_time_s / 2)
        continue

      temp_f = c_to_f(temp_c)
      print(f'temp is {temp_c}c, {temp_f}f')

      age_since_last_notification = int(time.time()) - last_notification_s
      if age_since_last_notification > periodic_report_s:
        try:
          print(f'Sending periodic notification because {age_since_last_notification} seconds have passed since last message (which is > {periodic_report_s} seconds for the periodic report)')
          pushover_client.send_message(f'InkBird temperature: {temp_f}f', title=f'InkBird temperature: {temp_f}f')
          last_notification_s = int(time.time())
        except:
          traceback.print_exc()
          pushover_client = pushover.Client(pushover_user_key, api_token=pushover_api_token)
        
        await asyncio.sleep(temp_measure_poll_time_s)
        continue

      temp_is_acceptable = temp_f < max(acceptable_temp_f_bounds) and temp_f > min(acceptable_temp_f_bounds)

      if not temp_is_acceptable:
        if age_since_last_notification < min_notification_delay_s:
          print(f'Not notifying because we did so {age_since_last_notification} seconds ago and we must wait at least {min_notification_delay_s}')
          await asyncio.sleep(temp_measure_poll_time_s)
          continue
        try:
          pushover_client.send_message(f'InkBird temperature alert: {temp_f}f', title=f'InkBird temperature alert: {temp_f}f')
          last_notification_s = int(time.time())
        except:
          traceback.print_exc()
          pushover_client = pushover.Client(pushover_user_key, api_token=pushover_api_token)

      await asyncio.sleep(temp_measure_poll_time_s)


if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal_handler)
  asyncio.run(main())


