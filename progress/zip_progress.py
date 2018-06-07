import re
import subprocess


class WgetRunner(object):
    """
    Usage:

        runner = WgetRunner()
        def status_handler(old, new):
            print "From {0} to {1}".format(old, new)

        runner.run('wget -c ...', status_handler=status_handler)

    """
    re_error = re.compile(r".+ERROR", re.U | re.I)
    re_retrieved = re.compile("The file is already fully retrieved",re.U | re.I)
    re_progress = re.compile(r".+ (?P<progress>\d{1,3})%.+", re.U | re.I)

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
        new_percents = 0

        while True:
            line = pipe.stdout.readline().strip()
            if line == '' and pipe.poll() is not None:  # process end
                break

            error = self.re_error.match(line)
            if error:
                print(line)
                break

            retrieved = self.re_retrieved.match(line)
            if retrieved:
                print(line)
                if callable(status_handler):
                    status_handler(100, 100)
                break

            match = self.re_progress.match(line)
            if match:
                new_percents = match.groupdict().get("progress")
                print(new_percents)

            if new_percents != percents:
                if callable(status_handler):
                    status_handler(percents, new_percents)
                percents = new_percents
        pipe.wait()
        if error:
            print("error {0}".format(line))

    @staticmethod
    def get_percent(linestr):
        match = re.search(r"(?P<progress>\d{1,3})%", linestr, re.I | re.L)
        if match:
            # print(match.group())
            progress = match.groupdict().get("progress")
            return progress
        return -1




def status_handler(old, new):
    pass
    # print("From {0} to {1}".format(old, new))



if __name__ == "__main__":
    runner = WgetRunner()

    # unzip
    commad = "7z -c {0} -y -o{1}".format("http://www.futurecrew.com/skaven/song_files/mp3/razorback.mp3", "unzip")



    runner.run_session(command=commad,
                       status_handler=status_handler)