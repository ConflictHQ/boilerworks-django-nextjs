from django.db.models import QuerySet


class Search:

    @classmethod
    def do_search(cls, qs: QuerySet, query='', more_filters=None):
        """
        Very basic search. We will need to add more features later.
        """
        if more_filters:
            qs = qs.filter(**more_filters)

        if query:
            query = [q for q in query.split(' ') if q]
            for q in query:
                qs = qs.filter(search__icontains=q)

        return qs
