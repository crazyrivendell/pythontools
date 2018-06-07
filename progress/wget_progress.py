import re, os
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


def download_v2_(url, rid, task_pk, base_percent, scale_percent, callback_handler):
    """
    progress support
    """
    print("download url:{0}".format(url))
    origin_name = os.path.basename(url)
    key_name, ext = os.path.splitext(origin_name)

    dir = os.path.join(rid[0:2], rid[2:4], rid)
    path = os.path.join(dir, rid + ext)
    if os.path.exists(path):
        print("{0} exist".format(path))
        return
    if not os.path.exists(dir):
        os.makedirs(dir)

    command = "wget -c {0} -O {1}".format(url, path)

    pipe = subprocess.Popen(command, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)

    line = None
    error = None
    percents = 0
    new_percents = 0

    re_error = re.compile(r".+ERROR", re.U | re.I)
    re_retrieved = re.compile("The file is already fully retrieved", re.U | re.I)
    re_progress = re.compile(r".+ (?P<progress>\d{1,3})%.+", re.U | re.I)

    while True:
        line = pipe.stdout.readline().strip()

        if line == '' and pipe.poll() is not None:  # process end
            break

        error = re_error.match(line)
        if error:
            break

        retrieved = re_retrieved.match(line)
        if retrieved:
            if callable(callback_handler):
                callback_handler(task_pk, base_percent, scale_percent, 100)
            break

        match = re_progress.match(line)
        if match:
            new_percents = match.groupdict().get("progress")
        print(type(new_percents))
        if new_percents != percents:
            if callable(callback_handler):
                callback_handler(task_pk, base_percent, scale_percent, new_percents)
            percents = new_percents

    if error:
        print("error {0}".format(line))


def call_hander(task_pk, base_percent, scale_percent, new_percents):
    print("{0} {1} {2} {3}".format(task_pk, base_percent, scale_percent, new_percents))

if __name__ == "__main__":
    # runner = WgetRunner()
    #
    # commad = "wget -c {0}".format("http://v3.kandaovr.com/lvcjr3Q_5XEvZftn4RhT4IJzmS0G.7z")
    #
    # runner.run_session(command=commad,
    #                    status_handler=status_handler)

    download_v2_("http://v3.kandaovr.com/lvcjr3Q_5XEvZftn4RhT4IJzmS0G.7z","aabbcc",1,0,100, call_hander)