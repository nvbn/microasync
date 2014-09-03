from microasync.csp import loop, go, Delay
from microasync.device import Ultrasonic


@go
def main():
    ultrasonic = Ultrasonic('X7', 'X6')
    while True:
        val = yield ultrasonic.distance_in_cm()
        print(val)
        yield Delay(1)

main()
loop()
