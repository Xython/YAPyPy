from abc import abstractmethod
import typing as t
T = t.TypeVar('T')

__all__ = ['Query']


class Query(t.Generic[T]):
    @abstractmethod
    def first(self) -> 't.Optional[T]':
        """
        apply the given filtering criterion to a copy
        of this :class:`.Query`, using SQL expressions.
        e.g.::
            session.query(MyClass).filter(MyClass.name == 'some name')
        Multiple criteria may be specified as comma separated; the effect
        is that they will be joined together using the :func:`.and_`
        function::
            session.query(MyClass).\
                filter(MyClass.name == 'some name', MyClass.id > 5)
        The criterion is any SQL expression object applicable to the
        WHERE clause of a select.   String expressions are coerced
        into SQL expression constructs via the :func:`.text` construct.
        .. seealso::
            :meth:`.Query.filter_by` - filter on keyword expressions.
        """
        pass

    @abstractmethod
    def filter(self, *criterion) -> 'Query[T]':
        """
        apply the given filtering criterion to a copy
    of this :class:`.Query`, using SQL expressions.
    e.g.::
        session.query(MyClass).filter(MyClass.name == 'some name')
    Multiple criteria may be specified as comma separated; the effect
    is that they will be joined together using the :func:`.and_`
    function::
        session.query(MyClass).\
            filter(MyClass.name == 'some name', MyClass.id > 5)
    The criterion is any SQL expression object applicable to the
    WHERE clause of a select.   String expressions are coerced
    into SQL expression constructs via the :func:`.text` construct.
    .. seealso::
        :meth:`.Query.filter_by` - filter on keyword expressions.
        """
        pass

    @abstractmethod
    def filter_by(self, **kwargs) -> 'Query[T]':
        """
        apply the given filtering criterion to a copy
    of this :class:`.Query`, using keyword expressions.
    e.g.::
        session.query(MyClass).filter_by(name = 'some name')
    Multiple criteria may be specified as comma separated; the effect
    is that they will be joined together using the :func:`.and_`
    function::
        session.query(MyClass).\
            filter_by(name = 'some name', id = 5)
    The keyword expressions are extracted from the primary
    entity of the query, or the last entity that was the
    target of a call to :meth:`.Query.join`.
    .. seealso::
        :meth:`.Query.filter` - filter on SQL expressions.
        """
        pass

    @abstractmethod
    def all(self) -> 't.List[T]':
        pass

    @abstractmethod
    def order_by(self, *criterion) -> 'Query[T]':
        """
        apply one or more ORDER BY criterion to the query and return
        the newly resulting ``Query``
        All existing ORDER BY settings can be suppressed by
        passing ``None`` - this will suppress any ORDER BY configured
        on mappers as well.
        Alternatively, passing False will reset ORDER BY and additionally
        re-allow default mapper.order_by to take place.   Note mapper.order_by
        is deprecated.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Return a count of rows this Query would return.
        This generates the SQL for this Query as follows::
            SELECT count(1) AS count_1 FROM (
                SELECT <rest of query follows...>
            ) AS anon_1
        .. versionchanged:: 0.7
            The above scheme is newly refined as of 0.7b3.
        For fine grained control over specific columns
        to count, to skip the usage of a subquery or
        otherwise control of the FROM clause,
        or to use other aggregate functions,
        use :attr:`~sqlalchemy.sql.expression.func`
        expressions in conjunction
        with :meth:`~.Session.query`, i.e.::
            from sqlalchemy import func
            # count User records, without
            # using a subquery.
            session.query(func.count(User.id))
            # return count of user "id" grouped
            # by "name"
            session.query(func.count(User.id)).\
                    group_by(User.name)
            from sqlalchemy import distinct
            # count distinct "name" values
            session.query(func.count(distinct(User.name)))
        """

    @abstractmethod
    def limit(self, n: int) -> 'Query[T]':
        """Apply a ``LIMIT`` to the query and return the newly resulting ``Query``."""
        pass
