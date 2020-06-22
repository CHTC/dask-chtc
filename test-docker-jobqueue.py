from dask.distributed import Client
import dask.array as da

from dask_chtc import CHTCCluster

if __name__ == "__main__":
    with CHTCCluster() as cluster:
        cluster.scale(10)
        print(cluster)

        client = Client(cluster)
        print(client)

        x = da.random.random((10000, 10000), chunks=1000)

        y = (x ** 2).sum()

        print("\nCOMPUTATION", y, "\n")

        z = y.compute()

        print("\nRESULT", z, "\n")
