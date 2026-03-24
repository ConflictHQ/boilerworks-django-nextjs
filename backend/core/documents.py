"""
OpenSearch document definitions for core models.

Connection is configured in CoreConfig.ready() via setup_opensearch().
Indexing happens via post_save/post_delete signals registered there.
"""
from django.conf import settings
from opensearch_dsl import Document, Keyword, Text, connections


def setup_opensearch():
    """Configure the default opensearch-dsl connection from settings."""
    connections.create_connection(
        hosts=[settings.OPENSEARCH_URL],
        http_compress=True,
        use_ssl=False,
    )


class ProfileDocument(Document):
    """
    OpenSearch document for Profile full-text search.

    Indexed fields are kept intentionally light — only the fields
    needed for the multi_match search in UserFilterSet._filter_by_search.
    Add more fields here as needed; re-index with:
        python manage.py opensearch_index --rebuild
    """

    first_name = Text(fields={"keyword": Keyword()})
    last_name = Text(fields={"keyword": Keyword()})
    display_name = Text(fields={"keyword": Keyword()})
    email = Keyword()
    search = Text()

    class Index:
        name = "profiles"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        # Not using django-opensearch-dsl, so no model reference here;
        # indexing is handled manually via signals below.
        pass

    @classmethod
    def from_profile(cls, profile):
        email = profile.user.email if profile.user_id else ""
        return cls(
            meta={"id": str(profile.gid)},
            first_name=profile.first_name or "",
            last_name=profile.last_name or "",
            display_name=profile.display_name or "",
            email=email,
            search=" ".join(filter(None, [
                profile.first_name,
                profile.last_name,
                profile.display_name,
                email,
            ])),
        )

    @classmethod
    def index_profile(cls, profile):
        try:
            doc = cls.from_profile(profile)
            doc.save()
        except Exception:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to index profile %s", profile.gid, exc_info=True
            )

    @classmethod
    def delete_profile(cls, profile_gid):
        try:
            cls.get(id=str(profile_gid)).delete()
        except Exception:
            pass


def _on_profile_save(sender, instance, **kwargs):
    ProfileDocument.index_profile(instance)


def _on_profile_delete(sender, instance, **kwargs):
    ProfileDocument.delete_profile(instance.gid)


def register_profile_signals():
    from core.models.user import Profile
    from django.db.models.signals import post_delete, post_save

    post_save.connect(_on_profile_save, sender=Profile, weak=False)
    post_delete.connect(_on_profile_delete, sender=Profile, weak=False)
