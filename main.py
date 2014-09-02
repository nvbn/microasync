import reactive
import core


@core.go
def toggle_leds():
    for led in range(1, 5):
        yield reactive.Led(led).toggle()
    return 'OK'


@core.go
def main():
    switch = reactive.Switch()
    while True:
        for led in range(1, 5):
            yield switch.clicked()
            yield reactive.Led(led).toggle()


@core.go
def on_timer():
    timer = reactive.Timer(4, freq=1)
    while True:
        yield timer.when()
        result = yield toggle_leds()
        print(result)


main()
on_timer()
core.loop()
