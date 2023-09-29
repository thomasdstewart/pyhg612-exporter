#!/usr/bin/env python3
'''
pyhg612-exporter - Python HG612 Prometheus Exporter
Copyright 2023 Thomas Stewart <thomas@stewarts.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import os
import prometheus_client
import re
import socket
import sys
import telnetlib
import time
from pprint import pprint as pp

class HG612Metrics:
    def __init__(self, polling_interval_seconds=10):
        self.polling_interval_seconds = polling_interval_seconds

        self.dsl_max_rate_up = prometheus_client.Gauge('pyhg612_max_rate_up', 'Max Rate Up')
        self.dsl_max_rate_down = prometheus_client.Gauge('pyhg612_max_rate_down', 'Max Rate Down')
        self.bearerrate_up = prometheus_client.Gauge('pyhg612_bearerrate_up', 'Bearer Rate Up')
        self.bearerrate_down = prometheus_client.Gauge('pyhg612_bearerrate_down', 'Bearer Rate Down')
        self.snr_up = prometheus_client.Gauge('pyhg612_snr_up', 'SNR Up')
        self.snr_down = prometheus_client.Gauge('pyhg612_snr_down', 'SNR Down')
        self.attn_up = prometheus_client.Gauge('pyhg612_attn_up', 'Attn Up')
        self.attn_down = prometheus_client.Gauge('pyhg612_attn_down', 'Attn Down')
        self.pwr_up = prometheus_client.Gauge('pyhg612_pwr_up', 'Pwr Up')
        self.pwr_down = prometheus_client.Gauge('pyhg612_pwr_down', 'Pwr Down')
        self.fec_up = prometheus_client.Gauge('pyhg612_fec_up', 'FEC Up')
        self.fec_down = prometheus_client.Gauge('pyhg612_fec_down', 'FEC Down')
        self.crc_up = prometheus_client.Gauge('pyhg612_crc_up', 'CRC Up')
        self.crc_down = prometheus_client.Gauge('pyhg612_crc_down', 'CRC Down')


    def run_metrics_loop(self):
        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        self.get()
        self.parse()

        self.dsl_max_rate_up.set(self.maxrate[0])
        self.dsl_max_rate_down.set(self.maxrate[1])
        self.bearerrate_up.set(self.bearerrate[0])
        self.bearerrate_down.set(self.bearerrate[1])

        self.snr_up.set(self.snr[1])
        self.snr_down.set(self.snr[0])
        self.attn_up.set(self.attn[1])
        self.attn_down.set(self.attn[0])
        self.pwr_up.set(self.pwr[1])
        self.pwr_down.set(self.pwr[0])

        self.fec_up.set(self.errors[1])
        self.fec_down.set(self.errors[0])
        self.crc_up.set(self.errors[3])
        self.crc_down.set(self.errors[2])

    def get(self):
        host = os.getenv('MODEM_HOST', 'modem')
        user = os.getenv('MODEM_USER', 'admin')
        password = os.getenv('MODEM_PASSWORD', 'admin')

        try:
            tn = telnetlib.Telnet(host)
        except:
            print("error connecting")
            self.raw_data = ''
            return

        #conn = socket.create_connection(host, user),timeout=30)

        #tn.set_debuglevel(2)

        tn.read_until(b'Login:')
        tn.write(user.encode('ascii') + b'\n')
        tn.read_until(b'Password:')
        tn.write(password.encode('ascii') + b'\n')
        tn.read_until(b'ATP>')
        tn.write(b'sh\n')
        tn.read_until(b'# ')
        tn.write(b'xdslcmd info --stats\n')

        self.raw_data = tn.read_until(b'# ').decode('ascii')

        tn.write(b'exit\n')
        tn.read_until(b'ATP>')
        tn.write(b'exit\n')
        tn.read_until(b'exit from configuration console.')

        #print(self.raw_data)
        #sys.exit()

    def parse(self):
        #Sample output from working connection
        #self.raw_data = b'xdslcmd info --stats\r\nxdslcmd: ADSL driver and PHY status\r\nStatus: Showtime\r\nRetrain Reason:\t0\r\nLast initialization procedure status:\t0\r\nMax:\tUpstream rate = 26419 Kbps, Downstream rate = 68180 Kbps\r\nBearer:\t0, Upstream rate = 20000 Kbps, Downstream rate = 69441 Kbps\r\nBearer:\t1, Upstream rate = 0 Kbps, Downstream rate = 0 Kbps\r\nLink Power State:\tL0\r\nMode:\t\t\tVDSL2 Annex B\r\nVDSL2 Profile:\t\tProfile 17a\r\nTPS-TC:\t\t\tPTM Mode(0x0)\r\nTrellis:\t\tU:ON /D:ON\r\nLine Status:\t\tNo Defect\r\nTraining Status:\tShowtime\r\n\t\tDown\t\tUp\r\nSNR (dB):\t 5.1\t\t 9.8\r\nAttn(dB):\t 13.6\t\t 0.0\r\nPwr(dBm):\t 12.9\t\t 3.4\r\n\t\t\tVDSL2 framing\r\n\t\t\tBearer 0\r\nMSGc:\t\t-6\t\t20\r\nB:\t\t243\t\t239\r\nM:\t\t1\t\t1\r\nT:\t\t0\t\t64\r\nR:\t\t10\t\t0\r\nS:\t\t0.1119\t\t0.3819\r\nL:\t\t18161\t\t5028\r\nD:\t\t8\t\t1\r\nI:\t\t254\t\t120\r\nN:\t\t254\t\t240\r\nQ:\t\t8\t\t0\r\nV:\t\t0\t\t0\r\nRxQueue:\t\t75\t\t0\r\nTxQueue:\t\t15\t\t0\r\nG.INP Framing:\t\t18\t\t0\r\nG.INP lookback:\t\t15\t\t0\r\nRRC bits:\t\t0\t\t24\r\n\t\t\tBearer 1\r\nMSGc:\t\t154\t\t-6\r\nB:\t\t0\t\t0\r\nM:\t\t2\t\t0\r\nT:\t\t2\t\t0\r\nR:\t\t16\t\t0\r\nS:\t\t6.4000\t\t0.0000\r\nL:\t\t40\t\t0\r\nD:\t\t3\t\t0\r\nI:\t\t32\t\t0\r\nN:\t\t32\t\t0\r\nQ:\t\t0\t\t0\r\nV:\t\t0\t\t0\r\nRxQueue:\t\t0\t\t0\r\nTxQueue:\t\t0\t\t0\r\nG.INP Framing:\t\t0\t\t0\r\nG.INP lookback:\t\t0\t\t0\r\nRRC bits:\t\t0\t\t0\r\n\t\t\tCounters\r\n\t\t\tBearer 0\r\nOHF:\t\t0\t\t1887520\r\nOHFErr:\t\t492\t\t1238\r\nRS:\t\t1379798384\t\t3486891\r\nRSCorr:\t\t1045793\t\t0\r\nRSUnCorr:\t0\t\t0\r\n\t\t\tBearer 1\r\nOHF:\t\t17429665\t\t0\r\nOHFErr:\t\t0\t\t0\r\nRS:\t\t174296031\t\t0\r\nRSCorr:\t\t25\t\t0\r\nRSUnCorr:\t0\t\t0\r\n\r\n\t\t\tRetransmit Counters\r\nrtx_tx:\t\t277891628\t\t0\r\nrtx_c:\t\t73220\t\t0\r\nrtx_uc:\t\t15319\t\t0\r\n\r\n\t\t\tG.INP Counters\r\nLEFTRS:\t\t163\t\t0\r\nminEFTR:\t69414\t\t0\r\nerrFreeBits:\t296444911\t\t0\r\n\r\n\t\t\tBearer 0\r\nHEC:\t\t0\t\t0\r\nOCD:\t\t0\t\t0\r\nLCD:\t\t0\t\t0\r\nTotal Cells:\t3022157299\t\t0\r\nData Cells:\t466943772\t\t0\r\nDrop Cells:\t0\r\nBit Errors:\t0\t\t0\r\n\r\n\t\t\tBearer 1\r\nHEC:\t\t0\t\t0\r\nOCD:\t\t0\t\t0\r\nLCD:\t\t0\t\t0\r\nTotal Cells:\t0\t\t0\r\nData Cells:\t0\t\t0\r\nDrop Cells:\t0\r\nBit Errors:\t0\t\t0\r\n\r\nES:\t\t123\t\t546\r\nSES:\t\t1\t\t0\r\nUAS:\t\t27\t\t27\r\nAS:\t\t279967\r\n\r\n\t\t\tBearer 0\r\nINP:\t\t52.00\t\t0.00\r\nINPRein:\t1.00\t\t0.00\r\ndelay:\t\t0\t\t0\r\nPER:\t\t0.00\t\t6.13\r\nOR:\t\t0.01\t\t33.91\r\nAgR:\t\t69512.46\t20033.74\r\n\r\n\t\t\tBearer 1\r\nINP:\t\t4.50\t\t0.00\r\nINPRein:\t4.50\t\t0.00\r\ndelay:\t\t3\t\t0\r\nPER:\t\t16.06\t\t0.01\r\nOR:\t\t79.68\t\t0.01\r\nAgR:\t\t79.68\t0.01\r\n\r\nBitswap:\t94218/94218\t\t600/600\r\n\r\nTotal time = 1 days 5 hours 46 min 34 sec\r\nFEC:\t\t1045793\t\t0\r\nCRC:\t\t492\t\t1238\r\nES:\t\t123\t\t546\r\nSES:\t\t1\t\t0\r\nUAS:\t\t27\t\t27\r\nLOS:\t\t0\t\t0\r\nLOF:\t\t0\t\t0\r\nLOM:\t\t0\t\t0\r\nLatest 15 minutes time = 1 min 34 sec\r\nFEC:\t\t2\t\t0\r\nCRC:\t\t0\t\t0\r\nES:\t\t0\t\t0\r\nSES:\t\t0\t\t0\r\nUAS:\t\t0\t\t0\r\nLOS:\t\t0\t\t0\r\nLOF:\t\t0\t\t0\r\nLOM:\t\t0\t\t0\r\nPrevious 15 minutes time = 15 min 0 sec\r\nFEC:\t\t38\t\t0\r\nCRC:\t\t0\t\t0\r\nES:\t\t0\t\t0\r\nSES:\t\t0\t\t0\r\nUAS:\t\t0\t\t0\r\nLOS:\t\t0\t\t0\r\nLOF:\t\t0\t\t0\r\nLOM:\t\t0\t\t0\r\nLatest 1 day time = 5 hours 46 min 34 sec\r\nFEC:\t\t18765\t\t0\r\nCRC:\t\t0\t\t31\r\nES:\t\t0\t\t25\r\nSES:\t\t0\t\t0\r\nUAS:\t\t0\t\t0\r\nLOS:\t\t0\t\t0\r\nLOF:\t\t0\t\t0\r\nLOM:\t\t0\t\t0\r\nPrevious 1 day time = 24 hours 0 sec\r\nFEC:\t\t78741\t\t0\r\nCRC:\t\t0\t\t190\r\nES:\t\t0\t\t130\r\nSES:\t\t0\t\t0\r\nUAS:\t\t0\t\t0\r\nLOS:\t\t0\t\t0\r\nLOF:\t\t0\t\t0\r\nLOM:\t\t0\t\t0\r\nSince Link time = 3 days 5 hours 46 min 7 sec\r\nFEC:\t\t1045793\t\t0\r\nCRC:\t\t492\t\t1238\r\nES:\t\t123\t\t546\r\nSES:\t\t1\t\t0\r\nUAS:\t\t0\t\t0\r\nLOS:\t\t0\t\t0\r\nLOF:\t\t0\t\t0\r\nLOM:\t\t0\t\t0\r\n# '.decode('ascii')

        #Sample output from unplugged phone line
        #self.raw_data = b' '.decode('ascii')

        #Interesting lines:
        '''
        Max:	Upstream rate = 26419 Kbps, Downstream rate = 68180 Kbps
        Bearer:	0, Upstream rate = 20000 Kbps, Downstream rate = 69441 Kbps

                Down		Up
        SNR (dB):	 5.1		 9.8
        Attn(dB):	 13.6		 0.0
        Pwr(dBm):	 12.9		 3.4

        Total time = 1 days 5 hours 46 min 34 sec
        FEC:		1045793		0
        CRC:		492		1238
        '''

        maxrate = re.findall('Max:\s+Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps', self.raw_data)
        if(len(maxrate) == 1):
            if(len(maxrate[0]) == 2):
                self.maxrate = maxrate[0]
            else:
                self.maxrate = [0, 0]
        else:
            self.maxrate = [0, 0]

        bearerrate = re.findall('Bearer:\s+0, Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps', self.raw_data)
        if(len(bearerrate) == 1):
            if(len(bearerrate[0]) == 2):
                self.bearerrate = bearerrate[0]
            else:
                self.bearerrate = [0, 0]
        else:
            self.bearerrate = [0, 0]

        snr = re.findall('SNR \(dB\):\s+([.\d]+)\s+([.\d]+)+', self.raw_data)
        if(len(snr) == 1):
            if(len(snr[0]) == 2):
                self.snr = snr[0]
            else:
                self.snr = [0, 0]
        else:
            self.snr = [0, 0]

        attn = re.findall('Attn\(dB\):\s+([.\d]+)\s+([.\d]+)+', self.raw_data)
        if(len(attn) == 1):
            if(len(attn[0]) == 2):
                self.attn = attn[0]
            else:
                self.attn = [0, 0]
        else:
            self.attn = [0, 0]

        pwr = re.findall('Pwr\(dBm\):\s+([.\d]+)\s+([.\d]+)+', self.raw_data)
        if(len(pwr) == 1):
            if(len(pwr[0]) == 2):
                self.pwr = pwr[0]
            else:
                self.pwr = [0, 0]
        else:
            self.pwr = [0, 0]

        errors = re.findall('Total time = .*\r\nFEC:\s+(\d+)\s+(\d+)\r\nCRC:\s+(\d+)\s+(\d+)', self.raw_data)
        if(len(errors) == 1):
            if(len(errors[0]) == 4):
                self.errors = errors[0]
            else:
                self.errors = [0, 0, 0, 0]
        else:
            self.errors = [0, 0, 0, 0]


def main():
    polling_interval_seconds = int(os.getenv('POLLING_INTERVAL_SECONDS', '5'))
    exporter_port = int(os.getenv('EXPORTER_PORT', '8080'))

    app_metrics = HG612Metrics(
        polling_interval_seconds=polling_interval_seconds
    )
    prometheus_client.start_http_server(exporter_port)
    app_metrics.run_metrics_loop()


if __name__ == '__main__':
    main()

