import re
import subprocess
import math
import threading

class FFMPegRunner(object):
    """
    Usage:

        runner = FFMpegRunner()
        def status_handler(old, new):
            print "From {0} to {1}".format(old, new)

        runner.run('ffmpeg -i ...', status_handler=status_handler)

    """
    re_duration = re.compile('Duration: (\d{2}):(\d{2}):(\d{2}).(\d{2})[^\d]*', re.U)
    re_position = re.compile('time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})\d*', re.U | re.I)
    re_error = re.compile('Error', re.U | re.I)

    def run_session(self, command, status_handler=None):
        pipe = subprocess.Popen(command, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)

        line = None
        duration = None
        position = None
        error = None
        percents = 0

        while True:
            line = pipe.stdout.readline().strip()
            if line == '' and pipe.poll() is not None:  # process end
                break

            error = self.re_error.match(line)
            if error:
                break

            if duration is None:
                duration_match = self.re_duration.match(line)
                if duration_match:
                    print(duration_match)
                    duration = self.time2sec(duration_match)

            if duration:
                position_match = self.re_position.search(line)
                if position_match:
                    position = self.time2sec(position_match)
                    print(position)
                    print(type(position))

            new_percents = self.get_percent(position, duration)
            # print(new_percents)
            # print(type(new_percents))


            if new_percents != percents:
                if callable(status_handler):
                    status_handler(percents, new_percents)
                percents = new_percents
        pipe.wait()
        if error:
            print("error {0}".format(line))

    def get_percent(self, position, duration):
        if not position or not duration:
            return 0
        percent = int(math.floor(100 * position / duration))
        return 100 if percent > 100 else percent

    def time2sec(self, search):
        return sum([i**(2-i) * int(search.group(i+1)) for i in range(3)])


def status_handler(old, new):
    print("From {0} to {1}".format(old, new))



if __name__ == "__main__":
    runner = FFMPegRunner()

    runner.run_session('ffmpeg  -y -i /home/wuminlai/Work/study/python/pythontools/progress/test.mp4 -c:v libx265 -an -f mp4 /home/wuminlai/Work/study/python/pythontools/progress/test3.mp4',
                       status_handler=status_handler)