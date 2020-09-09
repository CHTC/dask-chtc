.. _installation:

.. py:currentmodule:: dask_chtc

Installing Dask-CHTC
====================

Dask-CHTC is a Python package that allows you to run
Dask clusters
and Jupyter notebook servers
on CHTC submit nodes.
To run Dask on CHTC, you will need to

#. Install a "personal" Python on a CHTC submit node.
#. Install whatever other packages you want, like
   ``numpy``, ``matplotlib``, ``dask-ml``, or ``jupyterlab``.
#. Install ``dask-chtc`` itself.

.. attention::

    We currently only support the Dask-CHTC workflow on the
    ``submit3.chtc.wisc.edu`` submit node.
    If you do not have an account on ``submit3.chtc.wisc.edu``, you will need to
    `request one <mailto:chtc@cs.wisc.edu>`_.


Install a Personal Python
-------------------------

You will need a Python installation on a CHTC submit node to run your code.
You will be able to manage packages in this Python installation just like
you would on your local machine, without needing to work with the CHTC
system administrators.

Since you do not have permission to install packages in the "system" Python
on CHTC machines (and since you should never do that anyway), you will need to
make a "personal" Python installation. We **highly recommend** doing this using
`Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_, a minimal
installation of Python and the ``conda``
`package manager <https://docs.conda.io/en/latest/>`_.

To create a Miniconda installation, first log in to a CHTC submit node
(via ``ssh``). Then, download the latest version of the Miniconda installer
using ``wget``:

.. code-block:: console

    $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

Run the installer using ``bash``:

.. code-block:: console

    $ bash Miniconda3-latest-Linux-x86_64.sh

The installer will ask you to accept a license agreement, and then ask you
several questions about how to install Miniconda itself.
We recommend that you **do** "initialize Miniconda3 by running conda init"
when prompted; this will cause Python you just installed to be your default
Python in future shell sessions (instead of the system Python).

You may need to begin a new shell session for the commands in the next sections
to work as expected.
To check that everything is hooked up correctly,
try running these commands:

.. code-block:: console

    $ which python
    $ which conda
    $ which pip

They should all resolve to paths inside the
Miniconda installation you just created.

Install Packages
----------------

Your personal Python installation will be used to run all of your code, so you
will need to install any packages that you depend on,
either inside your code (like ``numpy``)
or to do things like run Jupyter notebooks (provided by the ``jupyter`` package).

To install packages in your new personal Python installation, use the
``conda install`` command.
For example, to install ``numpy``, run

.. code-block:: console

    $ conda install numpy

You may occasionally need a package that isn't in the
`standard Anaconda channel <https://anaconda.org/anaconda/repo>`_.
Many more packages, and more up-to-date versions of packages,
are often available in the community-created
`conda-forge channel <https://conda-forge.org/>`_
channel.
For example, to install Dask from ``conda-forge`` instead of the default channel,
you would run

.. code-block:: console

    $ conda install -c conda-forge dask

where ``-c`` is short for ``--channel``.

Some packages are provided by other channels.
For example, PyTorch asks you to install from their own ``conda`` channel:

.. code-block:: console

    $ conda install -c pytorch pytorch

``conda`` is mostly compatible with ``pip``; if a package is not available
via ``conda`` at all, you can install it with ``pip`` as usual.


Install Dask-CHTC
-----------------

.. attention::

    These instructions will change in the future as Dask-CHTC stabilizes.

To install Dask-CHTC itself, run

.. code-block:: console

    $ pip install --upgrade git+https://github.com/CHTC/dask-chtc.git

To check that installation worked correctly, try running

.. code-block:: console

    $ dask-chtc --version
    Dask-CHTC version x.y.z

If you don't see the version message or some error occurs, try re-installing.
If that fails, please
`let us know <https://github.com/CHTC/dask-chtc/issues>`_.

What's Next?
------------

If you like working inside a Jupyter environment, you should read the next
two pages: :ref:`jupyter` and :ref:`networking`.

If you are going to run Dask non-interactively (i.e., through a normal Python
script, not a notebook), then you're almost ready to go.
Pull the :class:`CHTCCluster` and Dask client creation code from :doc:`example`
and start computing!
