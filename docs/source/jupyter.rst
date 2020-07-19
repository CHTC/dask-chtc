.. _jupyter:

.. py:currentmodule:: dask_chtc

Running Jupyter through Dask-CHTC
=================================

You may want to interact with your Dask cluster through a
`Jupyter notebook <https://jupyter.org/>`_.
Dask-CHTC provides a way to run a Jupyter notebook server on a CHTC submit node.

.. warning::

    **Do not** run Jupyter notebook servers on CHTC submit nodes except through
    the process described on this page.

.. attention::

    You will need to learn how to
    :ref:`forward ports over SSH <networking>`
    to actually connect to the Jupyter notebook servers that you will learn
    how to run here. We recommend skimming this page, then reading about
    port forwarding, then coming back here to try out the commands in full.

You can run a notebook server via the Dask-CHTC command line tool, via the
``jupyter`` subcommand.
The command line tool will run the notebook server as an HTCondor job.
To see the detailed documentation for this subcommand, run

.. code-block:: console

    $ dask-chtc jupyter --help
    Usage: dask-chtc jupyter [OPTIONS] COMMAND [ARGS]...

        [... long description cut ...]

        Commands:
          start   Start a Jupyter notebook server as a persistent HTCondor job.
          run     Run a Jupyter notebook server as an HTCondor job.
          status  Get information about your running Jupyter notebook server.
          stop    Stop a Jupyter notebook server that was started via "start".

The four sub-sub-commands of ``dask-chtc jupyter``
(``run``, ``start``, ``status``, and ``stop``)
let us run and interact with a Jupyter notebook server.
You can run
``dask-chtc jupyter <subcommand> --help``
to get detailed documentation on each of them, but for now, let's try out the
``run`` subcommand.

Using the ``run`` subcommand
----------------------------

The ``run`` subcommand is the simplest way to launch a Jupyter notebook server.
It is designed to mimic the behavior of running a Jupyter notebook server on
your local machine. Any command line arguments you pass to it will be
passed to the actual ``jupyter`` command line tool.

For example, if you normally start up a Jupyter Lab instance with ``jupyter
lab``. The equivalent command for Dask-CHTC is ``dask-chtc jupyter run lab``
command would be

.. code-block:: console

    $ dask-chtc jupyter run lab
    000 (7858010.000.000) 2020-07-13 10:38:46 Job submitted from host: <128.104.100.44:9618?addrs=128.104.100.44-9618+[2607-f388-107c-501-92e2-baff-fe2c-2724]-9618&alias=submit3.chtc.wisc.edu&noUDP&sock=schedd_4216_675f>
    001 (7858010.000.000) 2020-07-13 10:38:47 Job executing on host: <128.104.100.44:9618?addrs=128.104.100.44-9618+[2607-f388-107c-501-92e2-baff-fe2c-2724]-9618&alias=submit3.chtc.wisc.edu&noUDP&sock=starter_5948_a76b_2712469>
    [... Jupyter startup logs cut ...]
    [I 10:38:51.582 LabApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
    [C 10:38:51.587 LabApp]

        To access the notebook, open this file in a browser:
            file:///home/karpel/.local/share/jupyter/runtime/nbserver-2187556-open.html
        Or copy and paste one of these URLs:
            http://localhost:8888/?token=fedee94f539b0beea492bb358d549ed79025b714f3b308c4
         or http://127.0.0.1:8888/?token=fedee94f539b0beea492bb358d549ed79025b714f3b308c4

HTCondor job events outputs some diagnostic information into this output
stream. These messages may be helpful if your notebook server job is
unexpectedly interrupted.

Just like running ``jupyter lab``, if you press Control-C,
the notebook server will be stopped:

.. code-block:: console

    ^C
    [C 10:40:35.962 LabApp] received signal 15, stopping
    [I 10:40:35.963 LabApp] Shutting down 0 kernels
    004 (7858010.000.000) 2020-07-13 10:40:36 Job was evicted.
        (0) CPU times
            Usr 0 00:00:00, Sys 0 00:00:00  -  Run Remote Usage
            Usr 0 00:00:01, Sys 0 00:00:00  -  Run Local Usage
        0  -  Run Bytes Sent By Job
        0  -  Run Bytes Received By Job
    009 (7858010.000.000) 2020-07-13 10:40:36 Job was aborted.
        Shut down Jupyter notebook server (by user karpel)

You can think of this notebook server as being tied to your ``ssh`` session.
If your ``ssh`` session disconnects (either because you quit manually, or
because it timed out, or because you closed your laptop, or any number of
other possible reasons) **your notebook server will also stop**.
The next section will discuss how to run your notebook server in a more
persistent manner.


Using the ``start``, ``status``, and ``stop`` subcommands
----------------------------------------------------------

The ``start`` subcommand is similar to the ``run`` subcommand, except that
if you end the command by Control-C or your terminal session ending,
**the notebook server will not be stopped**.
The command will still "take over" your terminal, echoing log messages just
like the ``run`` subcommand did:

.. code-block:: console

    $ dask-chtc jupyter start lab
    000 (7858021.000.000) 2020-07-13 10:52:51 Job submitted from host: <128.104.100.44:9618?addrs=128.104.100.44-9618+[2607-f388-107c-501-92e2-baff-fe2c-2724]-9618&alias=submit3.chtc.wisc.edu&noUDP&sock=schedd_4216_675f>
    001 (7858021.000.000) 2020-07-13 10:52:51 Job executing on host: <128.104.100.44:9618?addrs=128.104.100.44-9618+[2607-f388-107c-501-92e2-baff-fe2c-2724]-9618&alias=submit3.chtc.wisc.edu&noUDP&sock=starter_5948_a76b_2713469>
    [... Jupyter startup logs cut ...]
    [I 10:52:56.060 LabApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
    [C 10:52:56.066 LabApp]

        To access the notebook, open this file in a browser:
            file:///home/karpel/.local/share/jupyter/runtime/nbserver-2209285-open.html
        Or copy and paste one of these URLs:
            http://localhost:8888/?token=3342f18a95d7d61c51a2b8cf80b836e932ac53f9ebdb3965
         or http://127.0.0.1:8888/?token=3342f18a95d7d61c51a2b8cf80b836e932ac53f9ebdb3965
    ^C

Even though we pressed Control-C, the notebook server will still be running.
We can look at the status of our notebook server job using the
``status`` subcommand, which will show us various diagnostic information
on both the Jupyter notebook server and the HTCondor job it is running inside:

.. code-block:: console

    $ dask-chtc jupyter status
    █ RUNNING  jupyter lab
    ├─ Contact Address: http://127.0.0.1:8888/?token=3342f18a95d7d61c51a2b8cf80b836e932ac53f9ebdb3965
    ├─ Python Executable: /home/karpel/.python/envs/dask-chtc/bin/python3.7
    ├─ Working Directory:  /home/karpel/dask-chtc
    ├─ Job ID: 7858021.0
    ├─ Last status change at:  2020-07-13 15:52:51+00:00 UTC (4 minutes ago)
    ├─ Originally started at: 2020-07-13 15:52:51+00:00 UTC (4 minutes ago)
    ├─ Output: /home/karpel/.dask-chtc/jupyter-logs/current.out
    ├─ Error:  /home/karpel/.dask-chtc/jupyter-logs/current.err
    └─ Events: /home/karpel/.dask-chtc/jupyter-logs/current.events

This may be particularly useful for recovering the contact address of a
notebook server that you started running in a previous ``ssh`` session.

To stop your notebook server, run

.. code-block:: console

    $ dask-chtc jupyter stop
    [C 11:02:57.820 LabApp] received signal 15, stopping
    [I 11:02:57.821 LabApp] Shutting down 0 kernels
    004 (7858021.000.000) 2020-07-13 11:02:58 Job was evicted.
        (0) CPU times
            Usr 0 00:00:00, Sys 0 00:00:00  -  Run Remote Usage
            Usr 0 00:00:01, Sys 0 00:00:00  -  Run Local Usage
        0  -  Run Bytes Sent By Job
        0  -  Run Bytes Received By Job
    009 (7858021.000.000) 2020-07-13 11:02:58 Job was aborted.
        Shut down Jupyter notebook server (by user karpel)


What's Next?
------------

Once you're able to
:ref:`connect to your Jupyter notebook server <networking>`,
you should move on to :doc:`example` to learn how to create a
:class:`CHTCCluster`.
