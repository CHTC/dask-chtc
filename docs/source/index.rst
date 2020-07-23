Dask-CHTC
=========

.. py:currentmodule:: dask_chtc


Dask-CHTC builds on top of
`Dask-Jobqueue <https://jobqueue.dask.org/>`_
to spawn
`Dask <https://distributed.dask.org/>`_
workers in the
`CHTC <http://chtc.cs.wisc.edu/>`_
`HTCondor pool <https://research.cs.wisc.edu/htcondor/>`_.
It also provides tools for
:ref:`running Jupyter notebook servers in a controlled way on CHTC submit nodes <jupyter>`,
which you may find helpful for providing an interactive
development environment to use Dask in.


.. note::

    If you're interested in using Dask at CHTC but have never used CHTC resources
    before, please
    `fill out the CHTC contact form <http://chtc.cs.wisc.edu/form>`_
    to get in touch with our Research Computing Facilitators.
    If you've already had an engagement meeting, send an email to
    `chtc@cs.wisc.edu <mailto:chtc@cs.wisc.edu>`_ and let them know you're interested
    in using Dask.

.. attention::

    We currently only support the Dask-CHTC workflow on the
    ``submit3.chtc.wisc.edu`` submit node.
    If you do not have an account on ``submit3.chtc.wisc.edu``, you will need to
    `request one <mailto:chtc@cs.wisc.edu>`_.

.. attention::

    Dask-CHTC is prototype software!
    If you notice any issues or have any suggestions for improvements,
    please write up a
    `GitHub issue <https://github.com/JoshKarpel/dask-chtc/issues>`_
    detailing the problem or proposal.
    We also recommend "watching" the
    `GitHub repository <https://github.com/JoshKarpel/dask-chtc>`_
    to keep track of new releases, and upgrading promptly when they occur.

These pages will walk you through the various aspects of using Dask-CHTC:

:doc:`installation`
    How to install Python and Dask-CHTC on a CHTC submit node.

:doc:`jupyter`
    How to use Dask-CHTC to run a Jupyter notebook server on a CHTC submit node.

:doc:`networking`
    Information on CHTC networking and
    how to forward ports over SSH,
    which will allow you to connect to
    Jupyter notebooks and Dask dashboards running on CHTC submit nodes.

:doc:`example`
    A brief example Jupyter notebook,
    showing how to start up a :class:`CHTCCluster`
    and use it to perform some calculations.

:doc:`docker`
    Information on how to build Docker images for use with Dask-CHTC.

:doc:`troubleshooting`
    Solutions and advice for tackling specific problems that might arise
    while using Dask-CHTC.

Detailed information on the Python API
and the associated command line tool
can be found on these pages:

:doc:`api`
    API documentation for ``dask_chtc``.

:doc:`cli`
    Documentation for the ``dask-chtc`` CLI tool.


.. toctree::
   :maxdepth: 2
   :hidden:

   self

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting Started

   installation
   jupyter
   networking
   example
   docker
   troubleshooting

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Interfaces

   api
   cli
