#!/usr/bin/python
# vim:set fileencoding=utf-8:
import sqlite3
from ._Struct import Struct
#
# python で sqlite3 を簡単に扱おう
#

__all__ = ['DB']

# 文字列に utf-8 があったときなど
class DBError(Exception):
    pass

class Result:
    def __init__(self, cur):
        self.cur = cur

    def Tuples(self):
        """Returns iterator of tuples"""
        return iter(self.cur)

    def Tuple(self, default=KeyError):
        """Returns a tuple of one record or default"""
        t = self.cur.fetchone()
        if t == None:
            if default is KeyError:
                raise KeyError("No matched record")
            return default
        assert self.cur.fetchone() == None, "More than one row"
        return t

    def Structs(self):
        """Returns iterator of Structs"""
        names = [x[0] for x in self.cur.description]
        while True:
            t = self.cur.fetchone()
            if t is None:
                break
            row = Struct(**dict(list(zip(names, t))))
            yield row

    def Struct(self, default=KeyError):
        """Returns a Struct of one record or default"""
        t = self.cur.fetchone()
        if t == None:
            if default is KeyError:
                raise KeyError("No matched record")
            return default
        assert self.cur.fetchone() == None, "More than one row"

        names = [x[0] for x in self.cur.description]
        row = Struct(**dict(list(zip(names, t))))
        return row

    def Cols(self):
        """Returns iterator of single columns"""
        while True:
            t = self.cur.fetchone()
            if t is None:
                break
            assert len(t) == 1, "Must be just one column"
            yield t[0]

    def Col(self, default=KeyError):
        """Returns one column of one record or default"""
        t = self.cur.fetchone()
        if t == None:
            if default is KeyError:
                raise KeyError("No matched record")
            return default
#        assert len(t) == 1, "Must be just one column"
        assert self.cur.fetchone() == None, "More than one row"
        return t

class ListResult(Result):
    def Tuples(self):
        return list(Result.Tuples(self))
    def Structs(self):
        return list(Result.Structs(self))
    def Cols(self):
        return list(Result.Cols(self))

class DB:
    def __init__(self, fname = None, **params):
        self.conn = None
        if fname is None:
            self.fname = ':memory:'
        else:
            self.fname = fname
        assert self.fname
        self.params = params

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # 例外が発生した
            self.Rollback()
        else:
            self.Commit()

    def __enter__(self):
        return self

    def _cursor(self):
        conn = getattr(self, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(self.fname, **self.params)
            self.conn = conn

        cur = conn.cursor()
        return cur

    def Commit(self):
        conn = getattr(self, 'conn', None)
        if conn:
            conn.commit()

    def Rollback(self):
        conn = getattr(self, 'conn', None)
        if conn:
            conn.rollback()

    def _execute(self, query, params = ()):
        if not isinstance(params, (tuple, list)):
            params = (params, )

        cur = self._cursor()
        try:
            cur.execute(query, params)
        except sqlite3.ProgrammingError:
            raise DBError('文字列を unicode に変換してみてください')
        except:
            raise
        return cur

    def Query(self, query, params=()):
        return ListResult(Result(self._execute(query, params)))

    def Execute(self, query, params=()):
        return Result(self._execute(query, params))

    def _insert(self, sql, **params):
        keys = list(params.keys())
        names = ', '.join(["`%s`" % key for key in keys])
        values = [params[name] for name in keys]
        placeholder = ', '.join(['?'] * len(values))

        sql += ' (%s) VALUES (%s)' % (names, placeholder)
        try:
            cur = self._execute(sql, values)
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise
        except sqlite3.ProgrammingError:
            raise DBError('文字列を unicode に変換してみてください')

    def Insert(self, table, **params):
        sql = 'INSERT INTO %s' % table
        return self._insert(sql, **params)

    def Replace(self, table, **params):
        sql = 'REPLACE INTO %s' % table
        return self._insert(sql, **params)

    # name: テーブル名
    # tables: list
    #  [{name: カラム名, nametype: 型, primary: プライマリキー(True/False)
    #    auto: autoincrement(True/False), defaults: 初期値}]
    def CreateTable(self, name, tables):
        sql = 'CREATE TABLE IF NOT EXISTS `{0}`'.format(name)
        ts = []
        for p in tables:
            t = []
            if 'name' in p:
                t.append('`{name}`'.format(**p))
            else:
                raise DBError('テーブルのカラム名がない')
            tp = p.get('nametype', None)
            if tp:
                t.append(tp)
            if p.get('primary', False):
                t.append('PRIMARY KEY')
            if p.get('auto', False):
                t.append('AUTOINCREMENT')
            if p.get('defaults', None) is not None:
                t.append('DEFAULT {defaults}'.format(**p))
            ts.append(' '.join(t))
        sql += ' ({0})'.format(','.join(ts))
        self._execute(sql)

def test_db():
    db = DB()
    db.CreateTable('test', [
        {'name': 'id', 'nametype': 'INTEGER', 'primary': True, 'auto': True},
        {'name': 'msg', 'nametype': 'TEXT'},
        {'name': 'dummy', 'nametype': 'INTEGER', 'defaults': 0}
        ])
    db.Insert('test', msg = 'あーるーはれたーひーるーさがりー')
    db.Insert('test', msg = 'foo', dummy = 100)

    rslt = db.Query('SELECT * FROM test ORDER BY id').Tuples()
    assert len(rslt) == 2
    assert rslt[0][1] == 'あーるーはれたーひーるーさがりー'
    assert rslt[0][2] == 0
    assert rslt[1][1] == 'foo'
    assert rslt[1][2] == 100
    rslt = db.Query('SELECT * FROM test ORDER BY id').Structs()
    assert len(rslt) == 2
    assert rslt[0].msg == 'あーるーはれたーひーるーさがりー'
    assert rslt[0].dummy == 0
    assert rslt[1].msg == 'foo'
    assert rslt[1].dummy == 100

if __name__ == '__main__':
    try:
        test_db()
        print('%s ok' % __file__)
    except:
        print('%s fault' % __file__)
        import traceback
        traceback.print_exc()

