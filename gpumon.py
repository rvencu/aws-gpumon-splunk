# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  or in the "license" file accompanying this file. This file is distributed
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#  express or implied. See the License for the specific language governing
#  permissions and limitations under the License.


import urllib.request as urllib2
import requests
from pynvml import *
from datetime import datetime
from time import sleep, time

### CHOOSE REGION ####
EC2_REGION = 'us-east-1'

###CHOOSE NAMESPACE PARMETERS HERE###
my_NameSpace = 'GPU'

### CHOOSE PUSH INTERVAL ####
sleep_interval = 10

### CHOOSE STORAGE RESOLUTION (BETWEEN 1-60) ####
store_reso = 60

#Instance information
BASE_URL = 'http://169.254.169.254/latest/meta-data/'
INSTANCE_ID = urllib2.urlopen(BASE_URL + 'instance-id').read()
IMAGE_ID = urllib2.urlopen(BASE_URL + 'ami-id').read()
HOST = urllib2.urlopen(BASE_URL + 'local-ipv4').read()
INSTANCE_TYPE = urllib2.urlopen(BASE_URL + 'instance-type').read()
INSTANCE_AZ = urllib2.urlopen(BASE_URL + 'placement/availability-zone').read()
EC2_REGION = INSTANCE_AZ[:-1]

# Flag to push to Splunk
PUSH_TO_CW = True

def getPowerDraw(handle):
    powDraw = nvmlDeviceGetPowerUsage(handle) / 1000.0
    return float('%.2f' % powDraw)

def getTemp(handle):
    return nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)

def getUtilization(handle):
    return nvmlDeviceGetUtilizationRates(handle).gpu

def getMemUtilization(handle):
    mem_info = nvmlDeviceGetMemoryInfo(handle)
    return mem_info.used, mem_info.free

def logResults(i, util, mem_info_used, mem_info_free, pow_draw, temp):

    # splunk HTTP collector endpoint
    # curl https://hec.example.com:8088/services/collector/event -H "Authorization: Splunk B5A79AAD-D822-46CC-80D1-819F80D7BFB0" -d '{"event": "hello world"}'
    # data to be sent to api
    data = {
            "time":int( time() ),
            "event":{"InstanceId":INSTANCE_ID.decode("utf-8"),
                    "ImageId":IMAGE_ID.decode("utf-8"),
                    "InstanceType":INSTANCE_TYPE.decode("utf-8"),
                    "InstanceAZ":INSTANCE_AZ.decode("utf-8"),
                    "GPUNumber":str(i),
                    "GPU Usage":util,
                    "Memory Usage":mem_info_used,
                    "Memory Free":mem_info_free,
                    "Power Usage (Watts)":pow_draw,
                    "Temperature (C)":temp},
            "source":"aws-stability",
            "sourcetype":"gpumon",
            "host":HOST.decode("utf-8"),
            
        }
    print(data)
    
    # sending post request and saving response as response object
    headers = { "Content-type": "application/json", 
                "Accept": "text/plain",
                "Authorization":"Splunk b11bbc7a-61ed-424b-90f2-63cb69bdaf59"}
    x = requests.post('https://knn.laion.ai:8088/services/collector/event', json = data, headers = headers, verify=False)
    print(x.text)


nvmlInit()
deviceCount = nvmlDeviceGetCount()

def main():
    try:
        while True:
            # Find the metrics for each GPU on instance
            for i in range(deviceCount):
                handle = nvmlDeviceGetHandleByIndex(i)

                try:
                    pow_draw = getPowerDraw(handle)
                    temp = getTemp(handle)
                    util = getUtilization(handle)
                    mem_info_used, mem_info_free = getMemUtilization(handle)

                    logResults(i, util, mem_info_used, mem_info_free, pow_draw, temp)
                except NVMLError as err:
                    print(err)

            sleep(sleep_interval)

    finally:
        nvmlShutdown()

if __name__=='__main__':
    main()
