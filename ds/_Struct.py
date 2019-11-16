#!/usr/bin/python
# vim:set fileencoding=utf-8:

#
# python で 構造体みたいなやつ
#

__all__ = ['Struct']

class Struct():
    def __init__(self, *items, **attrs):
        for item in items:
            assert instance(item, (tuple, list))
            assert len(item) == 2
            name, value = item
            self.__dict__[name] = value
        self.__dict__.update(attrs)

    def __iter__(self):
        for name, value in self.__dict__.items():
            if name.startswith('_'):
                continue
            yield name, value

    def __len__(self):
        l = [name for name in list(self.__dict__.keys()) if not name.startswith('_')]
        return len(l)

    def __setitem__(self, name, value):
        self.__dict__[name] = value
        return value

    def __getitem__(self, name):
        return self.__dict__[name]

    def __contains__(self, value):
        return value in self.__dict__

    def get(self, name, default):
        return self.__dict__.get(name, default)

    def setdefault(self, name, value):
        if name not in self.__dict__:
            self.__dict__[name] = value
        return self.__dict__[name]

def test_struct():
    s = Struct()
    s = Struct(foo = 1, bar = 2)
    assert s.bar == 2
    assert len(s) == 2
    ls = list(iter(s))
    assert len(ls) == 2
    try:
        nothing = s.nothing
        assert False
    except AttributeError:
        pass
    s.hoge = 3
    assert len(s) == 3
    assert s.get('foooo', -1) == -1

if __name__ == '__main__':
    try:
        test_struct()
        print('%s ok' % __file__)
    except:
        print('%s fault' % __file__)
        import traceback
        traceback.print_exc()

