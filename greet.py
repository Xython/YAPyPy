class Greet:
    @classmethod
    def greet(cls):
        print('hello world')

    @classmethod
    def destruct(cls, data: dict):
        {'yapypy': yapypy} = data
        return yapypy


# try:
#     a = b
# except NameError as e:
#     a = 'name'
#
# assert a == 'name'
