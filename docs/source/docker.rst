.. _docker:

.. py:currentmodule:: dask_chtc

Building Docker Images for Dask-CHTC
====================================

Dask-CHTC runs all Dask workers inside Docker containers, which are built from
Docker images.
This guide won't cover how to build Docker images; innumerable tutorials are
available on the
`CHTC website <http://chtc.cs.wisc.edu/guides.shtml>`_
and the wider internet.
Our focus will be on the specific requirements for Dask-CHTC, with example
``Dockerfile``.

The first main requirement, perhaps unsurprisingly, is that ``dask`` needs to be
installed in your image so that it can run a Dask worker.
Secondarily, you'll also want to make sure various associated libraries
like ``lz4`` are installed.
You'll get warnings when the workers start for missing libraries
or version mismatches in these associated libraries; we recommend making sure
they are all resolved.

The other main requirement is that any library you use in your application
must also be available on the workers.
For example, if you ``import foobar`` in your code, the ``foobar`` package
must be available for import for the client as well as all of the workers.
(You can be a little more minimal than this, but it's not worth it
-- just make sure everything is installed.)


Images for CPU Workers
----------------------

Docker images for Dask workers that don't need to use GPUs are mostly the same
as normal Docker images. Dask provides a nice
`image <https://hub.docker.com/r/daskdev/dask>`_ which you can use directly
or build off of (the default image for Dask-CHTC is ``daskdev/dask:latest``).

Here's an example ``Dockerfile`` that installs some extra ``conda`` packages on
top of ``daskdev/dask``:

.. code-block:: dockerfile

    # Inherit from a Dask image. Make sure to use a specific tag, but not
    # necessarily this one - it's good to keep up to date!
    FROM daskdev/dask:2.20.0

    # Install various extra Python packages.
    RUN : \
     && conda install --yes \
        xarray \
        dask-ml \
     && conda clean --yes --all \
     && :


Images for GPU Workers
----------------------

If you want your workers to use GPUs,
**you must use a Docker image that inherits from an NVIDIA CUDA image**
(`their Docker Hub page <https://hub.docker.com/r/nvidia/cuda/>`_).
If you don't inherit from this image, your Dask worker will not be able to
use GPUs even if it lands on a HTCondor slot that has one
(the image works in concert with a special distribution of the Docker daemon
itself published by NVIDIA that CHTC runs on its GPU nodes).

You could inherit from one of those images yourself, or inherit from an image
that itself inherits from ``nvidia/cuda``.
For example, the
`PyTorch Docker images <https://hub.docker.com/r/pytorch/pytorch/>`_
inherit from the NVIDIA images, so you could use them as your base image.

Here's an example ``Dockerfile`` that builds off the PyTorch image:

.. code-block:: dockerfile

    # Inherit from a PyTorch image. Make sure to use a specific tag, but not
    # necessarily this one - it's good to keep up to date!
    FROM pytorch/pytorch:1.5.1-cuda10.1-cudnn7-runtime

    # Install various extra Python packages.
    RUN : \
     && conda install --yes \
        dask \
        dask-ml \
        lz4 \
        python-blosc \
        tini \
     && conda install --yes \
        -c conda-forge \
        skorch \
     && conda clean --yes --all \
     && :

    # Always run under tini!
    # See https://github.com/krallin/tini if you want to know why.
    # (The daskdev/dask image used above already does this.)
    ENTRYPOINT ["tini", "--"]
