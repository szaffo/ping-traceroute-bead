import subprocess
import shlex
import sys
import multiprocessing
import time
import os
import random
import datetime
import json

NUMBER_OF_PROCESSES = 40


def getDateString():
    date = datetime.datetime.now()
    return "{}{:02d}{:02d}".format(date.year, date.month, date.day)

class Worker:
    pings = {
        'date': getDateString(),
        'system': 'linux',
        'pings': []
    }

    traceroutes = {
        'date': getDateString(),
        'system': 'linux',
        'traces': []
    }

    def __init__(self, domain):
        self.domain = domain

    def traceroute(self):
        cmd = shlex.split("traceroute {} -m 30".format(self.domain))
        return self.job('traceroute', cmd)
    
    def ping(self):
        cmd = shlex.split("ping {} -c 10".format(self.domain))
        return self.job('ping', cmd)
        

    def job(self, job, cmd):
        process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, error = process.communicate()
        return {
            'pid': os.getpid(),
            'data': result.decode(),
            'job': job,
            'domain': self.domain,
            'error': error
        }


    def resultHandler(self, result):
        print("[{}] Process pid:{} finished with {} on {}".format(
            os.getpid(),
            result['pid'],
            result['job'],
            result['domain'])
        )

        if result['job'] == 'ping':
            self.__class__.pings['pings'].append({
                'target': result['domain'],
                'output': result['data']
            })
        
        elif result['job'] == 'traceroute':
            self.__class__.traceroutes['traces'].append({
                'target': result['domain'],
                'output': result['data']
            })


    def errorHandler(self, error):
        print("Got error: {}".format(error))

# ----------------------------------------
# Setup data

csvFile = sys.argv[1]

with open(csvFile, 'r') as f:
    domains = f.read()

domains = domains.strip().split('\n')
domains = [line.strip().split(',')[1]
           for line in (domains[0:10] + domains[-10:])]

pool = multiprocessing.Pool(processes=NUMBER_OF_PROCESSES)

for domain in domains:
    worker = Worker(domain)
    pool.apply_async(func=worker.ping, args=(), callback=worker.resultHandler, error_callback=worker.errorHandler)
    pool.apply_async(func=worker.traceroute, args=(), callback=worker.resultHandler, error_callback=worker.errorHandler)

pool.close()

try:
    pool.join()
except KeyboardInterrupt as e:
    print("STOPPED")


pool.terminate()
# [print(data, end='\n\n--------------------------\n\n')
#  for data in Worker.pings['pings']]
# print(len(Worker.pings['pings']))

with open('ping.json', 'w') as f:
    json.dump(Worker.pings, f, indent=4)

with open('traceroute.json', 'w') as f:
    json.dump(Worker.traceroutes, f, indent=4)

print('JOBS DONE')
