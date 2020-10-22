#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys, os, platform
import time, csv
import argparse
from collections import OrderedDict
import canopen

class CsvLogger:

    def __init__(self, filename):
        self.__file = filename
        self.__keys = {}

    @property
    def file(self):
        return self.__file
    @property
    def is_init(self):
        return True if self.keys else False
    @property
    def keys(self):
        return self.__keys

    def init(self, *keys):
        the_log_dir = os.path.dirname(self.file)
        if not os.path.exists(the_log_dir) and the_log_dir:
            os.makedirs(the_log_dir)
        self.__keys = list(keys)
        with open(self.file, 'w') as f:
            csv_writer = csv.DictWriter(f, fieldnames=self.keys)
            csv_writer.writeheader()

    def append(self, **dic_data):
        if not self.is_init:
            raise Exception("Logfile is not init.")
        for k in dic_data.keys():
            if k not in self._keys:
                raise Exception("LogKeyError: {} is not in {}".format(k, self.keys))
        with open(self.file, 'a') as f:
            csv_writer = csv.DictWriter(f, fieldnames=self.keys)
            csv_writer.writerow(dic_data)


class CanNetwork(canopen.Network):

    def send_message(self, can_id, data, remote=False):
        super(CanNetwork, self).send_message(can_id, data, remote=remote)
        if self.logger:
            l = self._canopen_filter(can_id, data, time.time())
            self.logger.append(**l)

    def notify(self, can_id, data, timestamp):
        super(CanNetwork, self).notify(can_id, data, timestamp)
        if self.logger:
            l = self._canopen_filter(can_id, data, timestamp)
            self.logger.append(**l)

    _logger = None
    @property
    def logger(self):
        return self._logger
    @logger.setter
    def logger(self, csv_logger_file):
        if not self.logger:
            self._logger = CsvLogger(csv_logger_file)
            log_keys = self.__log_template.keys()
            self.logger.init(*log_keys)
        else:
            raise ValueError("The logger is already set.")

    @property
    def __log_template(self):
        return OrderedDict([
                ("timestamp", None),
                ("can_id", None),
                ("data_length", None),
                ("hex_data", None),
                # above are the raw data
                ("separator", "|"),
                # separator for easy display
                ("service", None),
                # ("direction", None),
                ("target", None),
                # you could add more to do the pre filte
                ])

    def __canopen_filter(self, can_id, data, timestamp):
        ld = self.__log_template()
        try:
            ld['direction'] = direction_text
            ld['timestamp'] = timestamp
            ld['can_id'] = hex(can_id)
            ld['hex_data'] = " ".join([hex(b) for b in bytearray(data)])
            ld['data_length'] = len(data)
            if can_id == 0x000:
                ld['service'] = "NMT"
                try:
                    ld['target'] = hex(data[1])
                except:
                    ld['target'] = -255
            elif can_id > 0x000 and can_id < 0x080:
                ld['service'] = "unknown1"
                ld['target'] = -1
            elif can_id == 0x080:
                ld['service'] = "SYNC"
            elif can_id > 0x080 and can_id < 0x180:
                ld['service'] = "EMCY"
                ld['target'] = hex(can_id - 0x080)
            elif can_id >= 0x180 and can_id < 0x200:
                ld['service'] = "TPDO1"
                ld['target'] = hex(can_id - 0x180)
            elif can_id >= 0x200 and can_id < 0x280:
                ld['service'] = "RPDO1"
                ld['target'] = hex(can_id - 0x200)
            elif can_id >= 0x280 and can_id < 0x300:
                ld['service'] = "TPDO2"
                ld['target'] = hex(can_id - 0x280)
            elif can_id >= 0x300 and can_id < 0x380:
                ld['service'] = "RPDO2"
                ld['target'] = hex(can_id - 0x300)
            elif can_id >= 0x380 and can_id < 0x400:
                ld['service'] = "TPDO3"
                ld['target'] = hex(can_id - 0x380)
            elif can_id >= 0x400 and can_id < 0x480:
                ld['service'] = "RPDO3"
                ld['target'] = hex(can_id - 0x400)
            elif can_id >= 0x480 and can_id < 0x500:
                ld['service'] = "TPDO4"
                ld['target'] = hex(can_id - 0x480)
            elif can_id >= 0x500 and can_id < 0x580:
                ld['service'] = "RPDO4"
                ld['target'] = hex(can_id - 0x500)
            elif can_id >= 0x580 and can_id < 0x600:
                ld['service'] = "TSDO"
                ld['target'] = hex(can_id - 0x580)
            elif can_id >= 0x600 and can_id < 0x680:
                ld['service'] = "RSDO"
                ld['target'] = hex(can_id - 0x600)
            elif can_id >= 0x700 and can_id < 0x780:
                ld['service'] = "Bootup/Heartbeart"
                ld['target'] = hex(can_id - 0x700)
            else:
                ld['service'] = "unknown2"
                ld['target'] = -2
        except:
            import traceback
            logging.error(traceback.format_exc())
        return ld


def is_device_up(channel):
    if platform.system().lower() == "linux":
        with open('/sys/class/net/{}/operstate'.format(channel)) as f:
            t = f.read().split('\n')
            if t and t[0] == 'down':
                return False
    return True


def main(argv):
    parser = argparse.ArgumentParser(description="log data traffic via the CAN bus.")

    parser.add_argument("--channel", type=str, nargs=1, default='can0',
            help="The can device channel, default 'can0'.")
    parser.add_argument("--bitrate", type=int, nargs=1, default=500000,
            help="The can bus bitrate in int, default 500,000.")
    parser.add_argument("logfile", type=str)
    args = parser.parse_args(argv)

    can_network = CanNetwork()
    try:
        if not is_device_up(args.channel):
            print("CAN device is DOWN. Please up the CAN device first...")
            cmd = [''] * 4
            cmd[0] = 'sudo ip link set down {}'.format(args.channel)
            cmd[1] = 'sudo ip link set {} type can bitrate {}'.format(args.channel, args.bitrate)
            cmd[2] = 'sudo ip link set {} txqueuelen 10000'.format(args.channel)
            cmd[3] = 'sudo ip link set up {}'.format(args.channel)
            for c in cmd:
                print(c)
            sys.exit(1)
    except OSError:
        print("CAN device <{}> is missing...".format(args.channel))
        sys.exit(1)
    can_network = can_network.connect(bustype="socketcan",
            channel=args.channel, bitrate=args.bitrate)
    can_network.logger = args.logfile
    try:
        print("Logging the CAN Open data...")
        while True:
            time.sleep(1)
    except:
        import traceback
        traceback.print_exc()
    finally:
        pass

if __name__ == '__main__':
    main(sys.argv[1:])
