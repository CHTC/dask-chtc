from dask_jobqueue import HTCondorCluster
from dask.distributed import Client
import dask.array as da

if __name__ == '__main__':
    with HTCondorCluster(cores = 1, memory = "1 GB", disk = "1 GB") as cluster, Client(cluster) as client:
        cluster.scale(10)

        print(cluster)

        print(client)

        x = da.random.random((10000, 10000), chunks=(1000, 1000))

        y = (x ** 2).sum()

        print(y)

        z = y.compute()

        print(z)
