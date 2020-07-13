Dask-CHTC Documentation
=======================

.. py:currentmodule:: dask_chtc


Dask-CHTC builds on top of
`Dask-Jobqueue <https://jobqueue.dask.org/>`_
to launch
`Dask <https://distributed.dask.org/>`_
workers in the
`CHTC <http://chtc.cs.wisc.edu/>`_
`HTCondor pool <https://research.cs.wisc.edu/htcondor/>`_.


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


:doc:`installation`
    How to install Dask-CHTC.

:doc:`api`
    API documentation for ``dask_chtc``.

:doc:`cli`
    Documentation for the ``dask-chtc`` CLI tool.

:doc:`ports`
    Information on CHTC networking and
    how to forward ports over SSH,
    which will allow you to connect to
    Jupyter notebooks and Dask dashboards running on CHTC submit nodes.


.. toctree::
   :maxdepth: 2
   :hidden:

   self

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting Started

   installation

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   api
   cli
   ports
