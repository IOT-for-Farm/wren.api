from decouple import Config, RepositoryEnv

config = Config(repository=RepositoryEnv('.env'))
