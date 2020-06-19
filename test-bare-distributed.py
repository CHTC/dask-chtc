from dask.distributed import Client, LocalCluster
import dask.array as da

if __name__ == "__main__":
    with LocalCluster() as cluster, Client(cluster) as client:
        print(cluster)

        print(client)

        x = da.random.random((10000, 10000), chunks=(1000, 1000))

        y = (x ** 2).sum()

        print(y)

        z = y.compute()

        print(z)
