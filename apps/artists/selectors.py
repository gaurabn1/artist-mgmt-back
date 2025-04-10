from datetime import timedelta

from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.artists.serializers import ArtistSerializer
from apps.core.models import Artist
from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.selectors import ManagerSelector
from apps.users.utils import get_payload


class ArtistSelector:
    def __init__(self, request):
        self.request = request
        self.headers = request.headers
        self.page_size = request.query_params.get("page_size", 10)

    def get_artists_data(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if payload["role"] == "ARTIST":
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT 
                    a.name, count(DISTINCT al.uuid) as album, count(DISTINCT mu.uuid) as music
                    FROM artists_artist a
                    LEFT JOIN albums_album al ON a.uuid = al.owner_id
                    LEFT JOIN musics_music mu ON a.uuid = mu.artist_id
                    WHERE a.user_id = %s
                    GROUP BY a.name
                    """,
                    [payload["user_id"]],
                )
                artists = c.fetchall()
            if artists is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            artists_dict = convert_tuples_to_dicts(artists, ["name", "album", "music"])
            return Response(artists_dict, status=status.HTTP_200_OK)
        if payload["role"] == "SUPER_ADMIN":
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT 
                    a.name, count(DISTINCT al.uuid) as album, count(DISTINCT mu.uuid) as music
                    FROM artists_artist a
                    LEFT JOIN albums_album al ON a.uuid = al.owner_id
                    LEFT JOIN musics_music mu ON a.uuid = mu.artist_id
                    GROUP BY a.name
                    ORDER BY album DESC
                    LIMIT 5
                    """
                )
                artists = c.fetchall()
            if artists is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            artists_dict = convert_tuples_to_dicts(artists, ["name", "album", "music"])
            return Response(artists_dict, status=status.HTTP_200_OK)
        if payload["role"] == "ARTIST_MANAGER":
            user_id = payload["user_id"]
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT uuid
                    FROM profiles_userprofile
                    WHERE user_id = %s
                    """,
                    [user_id],
                )
                manager = c.fetchone()
                if manager is None:
                    return Response(status=status.HTTP_404_NOT_FOUND)

                c.execute(
                    """
                SELECT
                a.name, count(DISTINCT al.uuid) as album, count(DISTINCT mu.uuid) as music
                FROM artists_artist a
                LEFT JOIN albums_album al ON a.uuid = al.owner_id
                LEFT JOIN musics_music mu ON a.uuid = mu.artist_id
                WHERE a.manager_id = %s
                GROUP BY a.name
                ORDER BY album DESC
                LIMIT 4
                """,
                    [manager[0]],
                )
                artists = c.fetchall()
                if artists is None:
                    return Response(status=status.HTTP_404_NOT_FOUND)
            artists_dict = convert_tuples_to_dicts(artists, ["name", "album", "music"])
            return Response(artists_dict, status=status.HTTP_200_OK)

    def get_artists_count_manager(self, manager_id):
        time_15_minutes_ago = timezone.now() - timedelta(minutes=15)
        with connection.cursor() as c:
            c.execute(
                """
            SELECT
                (SELECT count(*) FROM artists_artist WHERE manager_id = %s),
                (SELECT count(*) FROM artists_artist WHERE created_at > %s AND manager_id = %s);
            """,
                [manager_id, time_15_minutes_ago, manager_id],
            )
            artist_result = c.fetchone()
            c.execute(
                """
            SELECT
                (
                SELECT count(a.*) FROM albums_album a
                LEFT JOIN artists_artist ar ON a.owner_id = ar.uuid
                WHERE ar.manager_id = %s
                ),
                (
                SELECT count(a.*) FROM albums_album a
                LEFT JOIN artists_artist ar ON a.owner_id = ar.uuid
                WHERE a.created_at > %s AND ar.manager_id = %s
                );
                """,
                [manager_id, time_15_minutes_ago, manager_id],
            )
            album_result = c.fetchone()
            c.execute(
                """
            SELECT
                (
                SELECT count(m.*) FROM musics_music m
                LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                WHERE ar.manager_id = %s
                ),
                (
                SELECT count(m.*) FROM musics_music m
                LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                WHERE ar.manager_id = %s
                AND m.created_at > %s
                );
                """,
                [manager_id, manager_id, time_15_minutes_ago],
            )
            music_result = c.fetchone()
        if artist_result is None or album_result is None or music_result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "artist_count": artist_result[0],
                "artists_last_15_minutes": artist_result[1],
                "album_count": album_result[0],
                "albums_last_15_minutes": album_result[1],
                "music_count": music_result[0],
                "musics_last_15_minutes": music_result[1],
            },
            status=status.HTTP_200_OK,
        )

    def get_artists_count_artist(self, artist_id):
        time_15_minutes_ago = timezone.now() - timedelta(minutes=15)
        with connection.cursor() as c:
            c.execute(
                """
                SELECT 
                (SELECT count(*) FROM albums_album WHERE owner_id = %s),
                (SELECT count(*) FROM albums_album WHERE created_at > %s AND owner_id = %s);
                """,
                [artist_id, time_15_minutes_ago, artist_id],
            )
            album_count = c.fetchone()
            c.execute(
                """
                SELECT 
                (SELECT count(*) FROM musics_music WHERE artist_id = %s),
                (SELECT count(*) FROM musics_music WHERE created_at > %s AND artist_id = %s);
                """,
                [artist_id, time_15_minutes_ago, artist_id],
            )
            music_count = c.fetchone()
        if album_count is None or music_count is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "album_count": album_count[0],
                "albums_last_15_minutes": album_count[1],
                "music_count": music_count[0],
                "musics_last_15_minutes": music_count[1],
            },
            status=status.HTTP_200_OK,
        )

    def get_users_count_admin(self):
        time_15_minutes_ago = timezone.now() - timedelta(minutes=15)
        with connection.cursor() as c:
            c.execute(
                """
                SELECT
                    (SELECT count(p.*) FROM profiles_userprofile p
                    JOIN core_user u ON u.uuid = p.user_id
                    WHERE u.role = 'ARTIST_MANAGER'),
                    (SELECT count(*) FROM profiles_userprofile p 
                    JOIN core_user u ON u.uuid = p.user_id
                    WHERE u.role = 'ARTIST_MANAGER' AND p.created_at > %s);
                """,
                [time_15_minutes_ago],
            )
            manager_result = c.fetchone()
            c.execute(
                """
                SELECT 
                    (SELECT count(*) FROM artists_artist),
                    (SELECT count(*) FROM artists_artist WHERE created_at > %s);
                """,
                [time_15_minutes_ago],
            )
            artist_result = c.fetchone()
            c.execute(
                """
                SELECT
                    (SELECT count(*) FROM albums_album),
                    (SELECT count(*) FROM albums_album WHERE created_at > %s);
                """,
                [time_15_minutes_ago],
            )
            album_result = c.fetchone()
            c.execute(
                """
                SELECT
                    (SELECT count(*) FROM musics_music),
                    (SELECT count(*) FROM musics_music WHERE created_at > %s);
                """,
                [time_15_minutes_ago],
            )
            music_result = c.fetchone()
        if artist_result is None or album_result is None or music_result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "manager_count": manager_result[0],
                "managers_last_15_minutes": manager_result[1],
                "artist_count": artist_result[0],
                "artists_last_15_minutes": artist_result[1],
                "album_count": album_result[0],
                "albums_last_15_minutes": album_result[1],
                "music_count": music_result[0],
                "musics_last_15_minutes": music_result[1],
            },
            status=status.HTTP_200_OK,
        )

    def get_artists_count(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_id = payload["user_id"]
        role = payload["role"]
        if role != "ARTIST_MANAGER" and role != "ARTIST" and role != "SUPER_ADMIN":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if role == "SUPER_ADMIN":
            return self.get_users_count_admin()

        if role == "ARTIST_MANAGER":
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT uuid
                    FROM profiles_userprofile
                    WHERE user_id = %s
                    """,
                    [user_id],
                )
                manager = c.fetchone()
                if manager is None:
                    raise APIException("Manager not found", status.HTTP_404_NOT_FOUND)
            manager_id = manager[0]
            return self.get_artists_count_manager(manager_id)

        if role == "ARTIST":
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT uuid
                    FROM artists_artist
                    WHERE user_id = %s
                    """,
                    [user_id],
                )
                artist = c.fetchone()
                if artist is None:
                    raise APIException("Artist not found", status.HTTP_404_NOT_FOUND)
                artist_id = artist[0]
            return self.get_artists_count_artist(artist_id)

    def get_currect_artist(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid
                FROM artists_artist
                WHERE user_id = %s
                """,
                [payload["user_id"]],
            )
            artist = c.fetchone()
            if artist is None:
                return Response(
                    {"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND
                )
        artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]
        if payload["role"] == "ARTIST":
            return self.get_artist_by_id(artist_dict["uuid"])

        if payload["role"] == "ARTIST_MANAGER":
            managerSelector = ManagerSelector(self.headers)
            return managerSelector.get_manager_by_id(payload["user_id"])
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_artists_artist(self):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT a.*
                FROM artists_artist a
                JOIN core_user u ON a.user_id = u.uuid
                """
            )

            artists = c.fetchall()
            columns = [col[0] for col in c.description]
        if artists is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        artists_dict = convert_tuples_to_dicts(artists, columns)
        artists_instances = [Artist(**artist) for artist in artists_dict]

        # paginate
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginated_artists = paginator.paginate_queryset(
            artists_instances, request=self.request
        )

        serializer = ArtistSerializer(paginated_artists, many=True)
        return Response(
            paginator.get_paginated_response(serializer.data).data,
            status=status.HTTP_200_OK,
        )

    def get_artists(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        role = payload.get("role", "")
        user_id = payload.get("user_id", "")

        if role != "ARTIST_MANAGER" and role != "ARTIST" and role != "SUPER_ADMIN":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if role == "ARTIST":
            return self.get_artists_artist()  # Get all artists

        if role == "SUPER_ADMIN":
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT * from artists_artist
                    """
                )
                artists = c.fetchall()
                columns = [col[0] for col in c.description]
                if artists is None:
                    return Response(
                        {"message": "No artists found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            artists_dict = convert_tuples_to_dicts(artists, columns)
            artists_instances = [Artist(**artist) for artist in artists_dict]

            # paginate
            paginator = PageNumberPagination()
            paginator.page_size = self.page_size
            paginated_artists = paginator.paginate_queryset(
                artists_instances, request=self.request
            )

            serializer = ArtistSerializer(paginated_artists, many=True)
            return Response(
                paginator.get_paginated_response(serializer.data).data,
                status=status.HTTP_200_OK,
            )

        # If role is an artist manager
        with connection.cursor() as c:
            c.execute(
                """
                SELECT a.* 
                FROM artists_artist a
                LEFT JOIN core_user u ON a.user_id = u.uuid
                LEFT JOIN profiles_userprofile m ON a.manager_id = m.uuid
                WHERE m.user_id = %s
                """,
                [user_id],
            )

            artists = c.fetchall()
            columns = [col[0] for col in c.description]
        if artists is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        artists_dict = convert_tuples_to_dicts(artists, columns)
        artists_instances = [Artist(**artist) for artist in artists_dict]

        # paginate
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginated_artists = paginator.paginate_queryset(
            artists_instances, request=self.request
        )

        serializer = ArtistSerializer(paginated_artists, many=True)
        return Response(
            paginator.get_paginated_response(serializer.data).data,
            status=status.HTTP_200_OK,
        )

    def get_artist_by_id(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT a.*
                FROM artists_artist a
                JOIN core_user u ON a.user_id = u.uuid
                WHERE a.uuid = %s
                """,
                [uuid],
            )
            artist = c.fetchone()
            columns = [col[0] for col in c.description]
        if artist is None:
            return None
        artist_dict = convert_tuples_to_dicts(artist, columns)
        artist_instance = [Artist(**artist) for artist in artist_dict]
        serializer = ArtistSerializer(artist_instance[0])
        return Response(serializer.data, status=status.HTTP_200_OK)
