.. _troubleshooting:

.. py:currentmodule:: dask_chtc

Troubleshooting
===============

Dask
----

``unsupported pickle protocol: 5``
++++++++++++++++++++++++++++++++++

If you get an error with the reason ``unsupported pickle protocol: 5``,
like

.. code-block:: pytb

    distributed.protocol.core - CRITICAL - Failed to deserialize
    Traceback (most recent call last):
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/core.py", line 130, in loads
        value = _deserialize(head, fs, deserializers=deserializers)
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/serialize.py", line 302, in deserialize
        return loads(header, frames)
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/serialize.py", line 64, in pickle_loads
        return pickle.loads(x, buffers=buffers)
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/pickle.py", line 75, in loads
        return pickle.loads(x)
    ValueError: unsupported pickle protocol: 5
    distributed.utils - ERROR - unsupported pickle protocol: 5
    Traceback (most recent call last):
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/utils.py", line 656, in log_errors
        yield
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/client.py", line 1221, in _handle_report
        msgs = await self.scheduler_comm.comm.read()
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/comm/tcp.py", line 206, in read
        allow_offload=self.allow_offload,
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/comm/utils.py", line 87, in from_frames
        res = _from_frames()
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/comm/utils.py", line 66, in _from_frames
        frames, deserialize=deserialize, deserializers=deserializers
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/core.py", line 130, in loads
        value = _deserialize(head, fs, deserializers=deserializers)
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/serialize.py", line 302, in deserialize
        return loads(header, frames)
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/serialize.py", line 64, in pickle_loads
        return pickle.loads(x, buffers=buffers)
      File "/home/karpel/miniconda3/lib/python3.7/site-packages/distributed/protocol/pickle.py", line 75, in loads
        return pickle.loads(x)
    ValueError: unsupported pickle protocol: 5

You are encountering an issue with mismatched Python versions between
your Dask client and the workers.
Python 3.8 introduced a new default protocol for Python's ``pickle`` module,
which Dask uses to move some kinds of data around.
In general, **you should always make sure that your Python versions match**.
For this specific issue, you just need to make sure that you are using
Python 3.7 or less (or Python 3.8 or greater) for both the Dask client
and the workers.

Jupyter
-------

Jupyter notebook server is stuck in the ``REMOVED`` state
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If something goes wrong during a normal ``dask-chtc jupyter stop``, you may
find that your notebook server will refuse to shut down.
The notebook server status will get stuck in ``REMOVED``, like this:

.. code-block:: console

    $ dask-chtc jupyter status
    █ REMOVED  jupyter lab
    ├─ Contact Address: http://127.0.0.1:8888/?token=d1717bce73ebc0e54ebeb16eeeef70811ead8eaae23e213c
    ├─ Python Executable: /home/karpel/miniconda3/bin/python
    ├─ Working Directory:  /home/karpel
    ├─ Job ID: 8138911.0
    ├─ Last status change at:  2020-07-19 21:34:02+00:00 UTC (23 minutes ago)
    ├─ Originally started at: 2020-07-19 18:57:07+00:00 UTC (3 hours ago)
    ├─ Output: /home/karpel/.dask-chtc/jupyter-logs/current.out
    ├─ Error:  /home/karpel/.dask-chtc/jupyter-logs/current.err
    └─ Events: /home/karpel/.dask-chtc/jupyter-logs/current.events

Because you can only run one notebook server at a time, this will prevent you
from launching a new notebook server.
To resolve this issue, you should run ``dask-chtc jupyter stop --force``:

.. code-block:: console

    $ dask-chtc jupyter stop --force
    000 (16453.000.000) 2020-07-21 11:58:25 Job submitted from host: <10.0.1.43:40415?addrs=10.0.1.43-40415+[2600-6c44-1180-1661-99fa-fc04-10e3-fd8d]-40415&alias=JKARPEL&noUDP&sock=schedd_20423_5f31>
    001 (16453.000.000) 2020-07-21 11:58:27 Job executing on host: <10.0.1.43:40415?addrs=10.0.1.43-40415+[2600-6c44-1180-1661-99fa-fc04-10e3-fd8d]-40415&alias=JKARPEL&noUDP&sock=starter_20464_7d39_11>
    005 (16453.000.000) 2020-07-21 11:58:30 Job terminated.
        (0) Abnormal termination (signal 9)
        (0) No core file
            Usr 0 00:00:00, Sys 0 00:00:00  -  Run Remote Usage
            Usr 0 00:00:00, Sys 0 00:00:00  -  Run Local Usage
            Usr 0 00:00:00, Sys 0 00:00:00  -  Total Remote Usage
            Usr 0 00:00:00, Sys 0 00:00:00  -  Total Local Usage
        0  -  Run Bytes Sent By Job
        0  -  Run Bytes Received By Job
        0  -  Total Bytes Sent By Job
        0  -  Total Bytes Received By Job

Always try stopping your notebook server with a plain ``stop`` command before
trying ``stop --force``;
``--force`` does not give the notebook server a chance
to shut down cleanly, so your Jupyter kernels may be interrupted while in the
middle of an operation.
