pacman
======

Update local pacman databases
-----------------------------

.. code-block:: text

    # pacman -Syu

Search repository for packages
------------------------------

.. code-block:: text

    $ pacman -Ss <pkg-name>

What package does <foo> come from?
----------------------------------

.. code-block:: text

    # pacman -Fy
    $ pacman -F <foo>

What depends on package <foo>?
------------------------------

.. code-block:: text

    $ pacman -Qi <foo>

Look at "Required By"
