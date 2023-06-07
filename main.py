from flask import Flask, render_template, request
import epson_projector as epson
from epson_projector.const import (PWR_OFF)
import asyncio
import aiohttp
import ipaddress

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shut_down', methods=['GET'])
def raise_volume():
    info_messages = asyncio.run(main())
    return '<br>'.join(info_messages)

async def main():
    async with aiohttp.ClientSession() as session:
        return await run(session)

async def run(websession):
    network = ipaddress.ip_network('172.16.16.0/24')
    starting_ip = ipaddress.IPv4Address('172.16.16.100')
    concurrency_limit = 25

    semaphore = asyncio.Semaphore(concurrency_limit)

    tasks = [
        turn_off_projector(websession, str(ip), semaphore)
        for ip in network
        if ip >= starting_ip
    ]
    results = await asyncio.gather(*tasks)
    return [result for result in results if result is not None]

async def turn_off_projector(websession, ip, semaphore):
    async with semaphore:
        try:
            projector = epson.Projector(
                host=ip,
                websession=websession
            )
            data = await projector.send_command(PWR_OFF)
            info = f"Projector at {ip} turned off: {data}"
            print(info)
            return info
        except Exception as e:
            info = f"Error turning off projector at {ip}: {e}"
            print(info)
            return None

if __name__ == '__main__':
    app.run(debug=True)
