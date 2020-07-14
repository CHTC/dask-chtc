# Dask-CHTC

[![Documentation Status](https://readthedocs.org/projects/dask-chtc/badge/?version=latest)](https://dask-chtc.readthedocs.io/en/latest/?badge=latest)
![GitHub issues](https://img.shields.io/github/issues/JoshKarpel/dask-chtc)
![GitHub pull requests](https://img.shields.io/github/issues-pr/JoshKarpel/dask-chtc)
![tests](https://github.com/JoshKarpel/dask-chtc/workflows/tests/badge.svg)

Dask-CHTC builds on top of
[Dask-Jobqueue](https://jobqueue.dask.org/)
to spawn
[Dask](https://distributed.dask.org/)
workers in the
[CHTC](http://chtc.cs.wisc.edu/)
[HTCondor pool](https://research.cs.wisc.edu/htcondor/).
Full documentation is available
[here](https://dask-chtc.readthedocs.io).

Dask-CHTC also provides tools for
running Jupyter notebook servers in a controlled way on CHTC submit nodes,
which you may find helpful for providing an interactive
development environment to use Dask in.

If you're interested in using Dask at CHTC but have never used CHTC resources
before, please
[fill out the CHTC contact form](http://chtc.cs.wisc.edu/form>)
to get in touch with our Research Computing Facilitators.
If you've already had an engagement meeting, send an email to
[chtc@cs.wisc.edu](mailto:chtc@cs.wisc.edu) and let them know you're interested
in using Dask.

Dask-CHTC is prototype software!
If you notice any issues or have any suggestions for improvements,
please write up a
[GitHub issue](https://github.com/JoshKarpel/dask-chtc/issues)
detailing the problem or proposal.
We also recommend "watching" the GitHub repository to keep track of
new releases and upgrading promptly when they occur.
