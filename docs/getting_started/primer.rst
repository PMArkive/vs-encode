============
Quick Primer
============

.. _primer:

VapourSynth scripts are all written using Python. This includes vs-encode.
To write a basic VapourSynth script, there are a couple fundamentals you must understand about Python.
This page is written to give you a very basic overview, as well as to explain some common terminology.

Before you begin, I highly encourage you read `this <https://wiki.python.org/moin/BeginnersGuide/NonProgrammers>`_ page.
This includes links to a lot of rudimentary Python exercises and learning material.

-----------
Basic usage
-----------

vs-encode is a Python module,
which means you must import it into your script
before it can be accessed.
You can import it by doing the following:

.. code-block:: py

    import vsencode

Simple, right?
But writing "vsencode" every time is cumbersome,
so we recommend you give it an alias.

.. code-block:: py

    import vsencode as vse

.. note::

    The rest of the documentation will assume you alias vs-encode as `vse`.

With the module now imported,
you can call functions in your script by referencing the module
and writing the function name behind it.

.. code-block:: py

    import vsencode as vse

    SRC = vse.Source("PATH/TO/YOUR/VIDEO")

.. TODO: Continue writing a basic example.
