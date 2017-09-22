def read(filename, binary=True):
    with open(filename, 'rb' if binary else 'r') as f:
        return f.read()
