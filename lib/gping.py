#! usr/bin/env python3

import subprocess
from subprocess import PIPE, CalledProcessError
import os, sys, math

def exit(f):
    def exit_wrap(*args, **kwargs):
        try:
            ret = f(*args, **kwargs)
        except KeyboardInterrupt:
            print("Keyboard Exit :: Wrapping Up")
            sys.exit(0)
        return ret
    return exit_wrap


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=PIPE, universal_newlines=True)
    for stdout in iter(popen.stdout.readline, ""):
        yield stdout

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise CalledProcessError(return_code, cmd)

def parse(line):
    if "Pinging" in line:
        print("Beginning ping")
    elif "Reply from " in line:
        bit = int(line[line.find("bytes=")+6:line.find("time=")-1])*8
        time_s = 1/1000 * int(line[line.find("time=")+5:line.find("ms")])
        print("\/"*(math.ceil((1/(time_s*1000)) * (os.get_terminal_size()[0]-12))) + "| ", end="")
        if bit/time_s > 1000:
            print("{} Kb/s".format(int(bit/(time_s*1000))))
        elif bit/time_s > 1000000:
            print("{} Mb/s".format(int(bit/(time_s*1000000))))
        elif bit/time_s > 1000000000:
            print("GIGABIT")
        else:
            print("{} b/s".format(int(bit/time_s)))
    elif "Ping statistics for" in line:
        print("Ending ping")

@exit
def main(ip="8.8.8.8"):
    for line in execute(["ping", "-t", ip]):
        parse(line)

if __name__ == "__main__":
    try:
        main(ip=sys.argv[1])
    except IndexError:
        main()
