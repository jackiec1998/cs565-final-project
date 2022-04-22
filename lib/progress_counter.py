import math


def human_readable(n):
    millnames = ['', 'K', 'M', 'B', 'T']
    n = float(n)
    millidx = max(0, min(len(millnames)-1,
                         int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.3g}{}'.format(n / 10**(3 * millidx), millnames[millidx])


class ProgressCounter:
    def __init__(self, on_report):
        self.__counter = 0
        self.__pow = 0
        self.__milestone = 1

        self.on_report = on_report

    @property
    def count(self):
        return self.__counter

    def increment(self, n=1):
        self.__counter += n
        if self.__counter >= self.__milestone:
            self.on_report(self.__milestone)

        while self.__milestone < self.__counter:
            if self.__milestone == 10 ** (self.__pow + 1):
                self.__pow += 1
            self.__milestone += 10**max(self.__pow - 2, 0)
