microasync
===========

Green threads and CSP for micropython.

`Api documentation <http://microasync.readthedocs.org/>`_.


Installation
-------------

For installing run:

.. code-block:: bash

    MICROPYPATH='path-to-pyboard' pip-micropython install microasync


Basic usage
------------

For basic usage you should create coroutines and start main loop.
For example, script that prints `ok!` every ten seconds:

.. code-block:: python

    from microasync.async import loop, coroutine, Delay


    @coroutine
    def main_coroutine():
        while True:
            print('ok!')
            yield Delay(10)


    main_coroutine()
    loop()


More examples:

- `examples in repo <https://github.com/nvbn/microasync/tree/master/examples/>`_;
- `green threads on pyboard <http://nvbn.github.io/2014/09/22/green-threads-on-pyboard/>`_;
- `csp on pyboard <http://nvbn.github.io/2014/10/05/csp-on-pyboard/>`_;
- `frp on pyboard <http://nvbn.github.io/2014/10/15/frp-on-pyboard/>`_.
