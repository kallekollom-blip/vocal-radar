import streamlit as st
import yt_dlp
import pandas as pd
import requests
import base64

from datetime import datetime, timedelta
from supabase import create_client


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Estonian Vocal Radar",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Estonian Vocal Radar")
st.caption("SoundCloud + YouTube + Spotify artistide scouting")


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )


supabase = get_supabase()


# ============================================================
# SPOTIFY
# ============================================================

@st.cache_data(ttl=300)
def spotify_token():

    client_id = st.secrets["spotify"]["client_id"]
    client_secret = st.secrets["spotify"]["client_secret"]

    credentials = f"{client_id}:{client_secret}"

    encoded = base64.b64encode(
        credentials.encode()
    ).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "client_credentials"
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()["access_token"]


def spotify_search(query, result_count):

    token = spotify_token()

    # Spotify max 10 per request
    wanted = min(result_count, 30)

    results = []

    offset = 0

    while len(results) < wanted:

        batch_size = min(
            10,
            wanted - len(results)
        )

        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers={
                "Authorization": f"Bearer {token}"
            },
            params={
                "q": query,
                "type": "track",
                "market": "EE",
                "limit": batch_size,
                "offset": offset
            },
            timeout=20
        )

        if response.status_code == 429:
            break

        response.raise_for_status()

        data = response.json()

        tracks = (
            data.get("tracks", {})
            .get("items", [])
        )

        if not tracks:
            break

        results.extend(tracks)

        offset += len(tracks)

        if len(tracks) < batch_size:
            break

    return results


# ============================================================
# USER
# ============================================================

marked_by = st.sidebar.radio(
    "Kes kasutab?",
    ["Kalle", "Vahur"]
)

st.sidebar.write(
    f"👤 Aktiivne kasutaja: **{marked_by}**"
)


# ============================================================
# NAVIGATION
# ============================================================

vaade = st.sidebar.radio(
    "Vaade",
    [
        "🔎 Otsi uusi",
        "🆕 Uued 7 päeva",
        "⭐ Lemmikud",
        "📩 Võta ühendust",
        "👀 Vaadatud",
        "❌ Ei sobi",
        "📋 Kõik salvestatud"
    ]
)


STATUS_LABELS = {
    "new": "🆕 Uus",
    "favorite": "⭐ Lemmik",
    "seen": "👀 Vaadatud",
    "contact": "📩 Võta ühendust",
    "reject": "❌ Ei sobi"
}

STATUS_OPTIONS = list(
    STATUS_LABELS.keys()
)


# ============================================================
# DATABASE
# ============================================================

def lae_salvestatud():

    try:

        response = (
            supabase
            .table("artists")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(
            f"Andmebaasi lugemise viga: {e}"
        )

        return []


def leia_track_url_jargi(track_url):

    try:

        response = (
            supabase
            .table("artists")
            .select("*")
            .eq(
                "track_url",
                track_url
            )
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except:
        return None


def salvesta_artist(
    artist_name,
    platform,
    track_name,
    track_url,
    profile_url,
    status,
    note,
    marked_by
):

    try:

        olemas = leia_track_url_jargi(
            track_url
        )

        data = {
            "artist_name": artist_name,
            "platform": platform,
            "track_name": track_name,
            "track_url": track_url,
            "profile_url": profile_url,
            "status": status,
            "note": note,
            "marked_by": marked_by
        }

        if olemas:

            (
                supabase
                .table("artists")
                .update(data)
                .eq(
                    "id",
                    olemas["id"]
                )
                .execute()
            )

        else:

            (
                supabase
                .table("artists")
                .insert(data)
                .execute()
            )

        return True

    except Exception as e:

        st.error(
            f"Salvestamise viga: {e}"
        )

        return False


def uuenda_salvestatud(
    artist_id,
    status,
    note,
    marked_by
):

    try:

        (
            supabase
            .table("artists")
            .update({
                "status": status,
                "note": note,
                "marked_by": marked_by
            })
            .eq(
                "id",
                artist_id
            )
            .execute()
        )

        return True

    except Exception as e:

        st.error(
            f"Uuendamise viga: {e}"
        )

        return False


# ============================================================
# SEARCH SETTINGS
# ============================================================

otsingud = [
    "Estonia",
    "Eesti",
    "Tallinn",
    "Tartu",
    "Pärnu",
    "Viljandi",
    "Rakvere",
    "Narva",

    "Estonian singer",
    "Estonian vocalist",
    "Estonian music",

    "Eesti laulja",
    "Eesti vokalist",
    "Eesti muusika",
    "Eesti cover",
    "Eesti demo",

    "Tallinn singer",
    "Tallinn vocalist",

    "Tartu singer",
    "Tartu vocalist"
]


eesti_marksonad = {
    "eesti": 35,
    "estonia": 35,
    "estonian": 35,
    "tallinn": 30,
    "tartu": 30,
    "pärnu": 30,
    "parnu": 30,
    "viljandi": 25,
    "rakvere": 25,
    "narva": 25,
    "haapsalu": 25,
    "kuressaare": 25,
    "võru": 25,
    "voru": 25,
    "jõhvi": 25,
    "johvi": 25,
}


# ============================================================
# HELPERS
# ============================================================

def saa_kuupaev(info):

    timestamp = info.get(
        "timestamp"
    )

    if timestamp:

        try:
            return datetime.fromtimestamp(
                timestamp
            )

        except:
            pass


    upload_date = info.get(
        "upload_date"
    )

    if upload_date:

        try:

            return datetime.strptime(
                upload_date,
                "%Y%m%d"
            )

        except:
            pass


    return None


def spotify_date(track):

    try:

        date_string = (
            track
            .get("album", {})
            .get("release_date")
        )

        precision = (
            track
            .get("album", {})
            .get(
                "release_date_precision",
                "day"
            )
        )

        if not date_string:
            return None


        if precision == "day":

            return datetime.strptime(
                date_string,
                "%Y-%m-%d"
            )


        if precision == "month":

            return datetime.strptime(
                date_string,
                "%Y-%m"
            )


        if precision == "year":

            return datetime.strptime(
                date_string,
                "%Y"
            )

    except:
        return None


def perioodi_paevad(valik):

    if valik == "Viimased 7 päeva":
        return 7

    if valik == "Viimased 30 päeva":
        return 30

    if valik == "Viimased 90 päeva":
        return 90

    if valik == "Viimased 365 päeva":
        return 365

    return None


def arvuta_skoor(info, otsing):

    tekst = " ".join([
        str(info.get("title", "")),
        str(info.get("uploader", "")),
        str(info.get("channel", "")),
        str(info.get("description", "")),
        str(info.get("genre", "")),
        str(info.get("tags", "")),
    ]).lower()

    return score_text(
        tekst,
        otsing
    )


def spotify_score(
    artist,
    track_name,
    album_name,
    query
):

    tekst = " ".join([
        artist,
        track_name,
        album_name
    ]).lower()

    return score_text(
        tekst,
        query
    )


def score_text(
    tekst,
    query
):

    skoor = 0
    pohjused = []

    juba = set()

    for sona, punktid in eesti_marksonad.items():

        if (
            sona in tekst
            and
            sona not in juba
        ):

            skoor += punktid

            juba.add(
                sona
            )

            pohjused.append(
                sona
            )


    if query.lower() in tekst:
        skoor += 10


    return (
        min(skoor, 100),
        pohjused
    )


def platvormid_otsimiseks(
    valik
):

    if valik == "SoundCloud":
        return ["SoundCloud"]

    if valik == "YouTube":
        return ["YouTube"]

    if valik == "Spotify":
        return ["Spotify"]

    if valik == "SoundCloud + YouTube":
        return [
            "SoundCloud",
            "YouTube"
        ]

    return [
        "SoundCloud",
        "YouTube",
        "Spotify"
    ]


def otsingu_prefix(
    platform,
    count
):

    if platform == "SoundCloud":

        return (
            f"scsearch{count}:"
        )


    if platform == "YouTube":

        return (
            f"ytsearch{count}:"
        )


    return ""


def vorminda_number(number):

    try:

        number = int(number)

        if number >= 1_000_000:

            return (
                f"{number / 1_000_000:.1f}M"
            )

        if number >= 1000:

            return (
                f"{number / 1000:.1f}K"
            )

        return str(number)

    except:

        return "?"


def vaiksuse_skoor(row):

    score = 0

    views = row[
        "Vaatamised"
    ]

    followers = row[
        "Jälgijad"
    ]


    if pd.notna(views):

        if views <= 1000:
            score += 50

        elif views <= 5000:
            score += 40

        elif views <= 10000:
            score += 30

        elif views <= 50000:
            score += 10


    if pd.notna(followers):

        if followers <= 500:
            score += 50

        elif followers <= 2000:
            score += 40

        elif followers <= 5000:
            score += 30

        elif followers <= 10000:
            score += 10


    return min(
        score,
        100
    )


# ============================================================
# SAVED VIEWS
# ============================================================

if vaade != "🔎 Otsi uusi":

    st.subheader(
        vaade
    )

    salvestatud = (
        lae_salvestatud()
    )


    if vaade == "⭐ Lemmikud":
        soovitud_status = "favorite"

    elif vaade == "📩 Võta ühendust":
        soovitud_status = "contact"

    elif vaade == "👀 Vaadatud":
        soovitud_status = "seen"

    elif vaade == "❌ Ei sobi":
        soovitud_status = "reject"

    else:
        soovitud_status = None


    if soovitud_status:

        salvestatud = [

            x
            for x in salvestatud

            if x.get("status")
            ==
            soovitud_status

        ]


    if vaade == "🆕 Uued 7 päeva":

        piir = (
            datetime.now()
            -
            timedelta(days=7)
        )

        uus_list = []

        for x in salvestatud:

            created_at = x.get(
                "created_at"
            )

            if not created_at:
                continue

            try:

                dt = datetime.fromisoformat(
                    created_at.replace(
                        "Z",
                        "+00:00"
                    )
                )

                dt = dt.replace(
                    tzinfo=None
                )

                if dt >= piir:

                    uus_list.append(
                        x
                    )

            except:
                pass

        salvestatud = uus_list


    if not salvestatud:

        st.info(
            "Selles vaates pole veel artiste."
        )


    for artist in salvestatud:

        st.subheader(
            f"{artist.get('artist_name', '')} – "
            f"{artist.get('track_name', '')}"
        )

        st.write(
            f"**Platvorm:** "
            f"{artist.get('platform', '')}"
        )

        current_status = (
            artist.get("status")
            or
            "new"
        )

        st.write(
            f"**Staatus:** "
            f"{STATUS_LABELS.get(current_status, current_status)}"
        )

        st.write(
            f"**Viimati märkis:** "
            f"{artist.get('marked_by', '')}"
        )

        current_note = (
            artist.get("note")
            or
            ""
        )


        col1, col2 = (
            st.columns(2)
        )


        with col1:

            if artist.get(
                "track_url"
            ):

                st.link_button(
                    "▶ Ava lugu",
                    artist["track_url"],
                    use_container_width=True
                )


        with col2:

            if artist.get(
                "profile_url"
            ):

                st.link_button(
                    "👤 Ava artist",
                    artist["profile_url"],
                    use_container_width=True
                )


        with st.expander(
            "✏️ Muuda staatust või märkust"
        ):

            uus_status = st.selectbox(
                "Staatus",
                STATUS_OPTIONS,
                index=(
                    STATUS_OPTIONS.index(
                        current_status
                    )
                    if current_status
                    in STATUS_OPTIONS
                    else 0
                ),
                format_func=lambda x:
                    STATUS_LABELS[x],
                key=(
                    f"saved_status_"
                    f"{artist['id']}"
                )
            )

            uus_markus = st.text_area(
                "Märkus",
                value=current_note,
                key=(
                    f"saved_note_"
                    f"{artist['id']}"
                )
            )

            if st.button(
                "💾 Salvesta muudatused",
                key=(
                    f"saved_update_"
                    f"{artist['id']}"
                ),
                use_container_width=True
            ):

                if uuenda_salvestatud(
                    artist["id"],
                    uus_status,
                    uus_markus,
                    marked_by
                ):

                    st.success(
                        "Uuendatud ✅"
                    )

                    st.rerun()

        st.divider()


# ============================================================
# SEARCH
# ============================================================

else:

    st.subheader(
        "🔎 Otsi uusi artiste"
    )

    salvestatud = (
        lae_salvestatud()
    )

    salvestatud_urlid = {

        x.get("track_url")

        for x in salvestatud

        if x.get("track_url")

    }

    salvestatud_map = {

        x.get("track_url"): x

        for x in salvestatud

        if x.get("track_url")

    }


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    with col1:

        platvorm = st.selectbox(
            "Platvorm",
            [
                "Kõik 3",
                "SoundCloud + YouTube",
                "SoundCloud",
                "YouTube",
                "Spotify"
            ]
        )


    with col2:

        tulemusi_otsingu_kohta = (
            st.slider(
                "Tulemusi iga otsingu kohta",
                5,
                30,
                10,
                5
            )
        )


    with col3:

        min_skoor = st.slider(
            "Minimaalne Eesti skoor",
            0,
            100,
            20,
            5
        )


    with col4:

        periood = st.selectbox(
            "Kui uusi näidata?",
            [
                "Viimased 7 päeva",
                "Viimased 30 päeva",
                "Viimased 90 päeva",
                "Viimased 365 päeva",
                "Kõik"
            ],
            index=1
        )


    st.write(
        "### 🌱 Väikese artisti filtrid"
    )


    col5, col6 = (
        st.columns(2)
    )


    with col5:

        max_vaatamised = st.number_input(
            "Maksimaalselt vaatamisi",
            min_value=0,
            value=10000,
            step=1000
        )


    with col6:

        max_jalgijad = st.number_input(
            "Maksimaalselt jälgijaid",
            min_value=0,
            value=5000,
            step=500
        )


    ainult_vaikesed = st.checkbox(
        "🌱 Ainult väikesed artistid",
        value=False
    )


    naita_teadmata = st.checkbox(
        "Näita teadmata statistikaga tulemusi",
        value=True
    )


    peida_juba_salvestatud = (
        st.checkbox(
            "🙈 Peida juba salvestatud lood",
            value=True
        )
    )


    sortimine = st.selectbox(
        "Sorteeri",
        [
            "Uusimad enne",
            "Kõrgeim Eesti skoor",
            "Kõige vähem vaatamisi",
            "Kõige vähem jälgijaid",
            "Väikseim artist"
        ]
    )


    if st.button(
        "🔎 OTSI",
        type="primary",
        use_container_width=True
    ):

        tulemused = []


        kasutatavad_platvormid = (
            platvormid_otsimiseks(
                platvorm
            )
        )


        koguarv = (
            len(otsingud)
            *
            len(kasutatavad_platvormid)
        )

        tehtud = 0

        progress = (
            st.progress(0)
        )

        status = (
            st.empty()
        )


        # ====================================================
        # YOUTUBE + SOUNDCLOUD
        # ====================================================

        opts = {
            "extract_flat": False,
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ignoreerrors": True
        }


        if (
            "YouTube"
            in kasutatavad_platvormid
            or
            "SoundCloud"
            in kasutatavad_platvormid
        ):

            with yt_dlp.YoutubeDL(
                opts
            ) as ydl:


                for platform_name in (
                    kasutatavad_platvormid
                ):

                    if platform_name == "Spotify":
                        continue


                    for otsing in otsingud:

                        status.write(
                            f"🔎 "
                            f"{platform_name}: "
                            f"**{otsing}**"
                        )


                        try:

                            query = (
                                otsingu_prefix(
                                    platform_name,
                                    tulemusi_otsingu_kohta
                                )
                                +
                                otsing
                            )


                            tulemus = (
                                ydl.extract_info(
                                    query,
                                    download=False
                                )
                            )


                            if (
                                tulemus
                                and
                                "entries"
                                in tulemus
                            ):

                                for info in (
                                    tulemus["entries"]
                                ):

                                    if not info:
                                        continue


                                    url = (
                                        info.get(
                                            "webpage_url"
                                        )
                                        or
                                        info.get(
                                            "original_url"
                                        )
                                        or
                                        info.get(
                                            "url"
                                        )
                                    )


                                    if not url:
                                        continue


                                    artist = (
                                        info.get(
                                            "uploader"
                                        )
                                        or
                                        info.get(
                                            "channel"
                                        )
                                        or
                                        "Tundmatu artist"
                                    )


                                    title = (
                                        info.get(
                                            "title"
                                        )
                                        or
                                        "Pealkiri puudub"
                                    )


                                    kuupaev = (
                                        saa_kuupaev(
                                            info
                                        )
                                    )


                                    skoor, pohjused = (
                                        arvuta_skoor(
                                            info,
                                            otsing
                                        )
                                    )


                                    tulemused.append({
                                        "Platvorm":
                                            platform_name,

                                        "Artist":
                                            artist,

                                        "Lugu":
                                            title,

                                        "Link":
                                            url,

                                        "Profiil":
                                            (
                                                info.get(
                                                    "uploader_url"
                                                )
                                                or
                                                info.get(
                                                    "channel_url"
                                                )
                                            ),

                                        "Kuupäev":
                                            kuupaev,

                                        "Skoor":
                                            skoor,

                                        "Põhjused":
                                            ", ".join(
                                                pohjused
                                            ),

                                        "Vaatamised":
                                            info.get(
                                                "view_count"
                                            ),

                                        "Jälgijad":
                                            info.get(
                                                "channel_follower_count"
                                            )
                                    })


                        except Exception as e:

                            st.warning(
                                f"{platform_name}: "
                                f"{otsing}: {e}"
                            )


                        tehtud += 1

                        progress.progress(
                            tehtud / koguarv
                        )


        # ====================================================
        # SPOTIFY
        # ====================================================

        if "Spotify" in kasutatavad_platvormid:


            for otsing in otsingud:


                status.write(
                    f"🟢 Spotify: "
                    f"**{otsing}**"
                )


                try:

                    tracks = spotify_search(
                        otsing,
                        tulemusi_otsingu_kohta
                    )


                    for track in tracks:


                        artists = track.get(
                            "artists",
                            []
                        )


                        artist_name = (
                            artists[0].get(
                                "name",
                                "Tundmatu artist"
                            )
                            if artists
                            else
                            "Tundmatu artist"
                        )


                        profile_url = None

                        if artists:

                            profile_url = (
                                artists[0]
                                .get(
                                    "external_urls",
                                    {}
                                )
                                .get(
                                    "spotify"
                                )
                            )


                        title = track.get(
                            "name",
                            "Pealkiri puudub"
                        )


                        album_name = (
                            track.get(
                                "album",
                                {}
                            )
                            .get(
                                "name",
                                ""
                            )
                        )


                        track_url = (
                            track.get(
                                "external_urls",
                                {}
                            )
                            .get(
                                "spotify"
                            )
                        )


                        if not track_url:
                            continue


                        kuupaev = (
                            spotify_date(
                                track
                            )
                        )


                        skoor, pohjused = (
                            spotify_score(
                                artist_name,
                                title,
                                album_name,
                                otsing
                            )
                        )


                        tulemused.append({
                            "Platvorm":
                                "Spotify",

                            "Artist":
                                artist_name,

                            "Lugu":
                                title,

                            "Link":
                                track_url,

                            "Profiil":
                                profile_url,

                            "Kuupäev":
                                kuupaev,

                            "Skoor":
                                skoor,

                            "Põhjused":
                                ", ".join(
                                    pohjused
                                ),

                            # Spotify ei anna
                            # YouTube'i stiilis
                            # vaatamiste arvu.
                            "Vaatamised":
                                None,

                            "Jälgijad":
                                None
                        })


                except Exception as e:

                    st.warning(
                        f"Spotify: "
                        f"{otsing}: {e}"
                    )


                tehtud += 1

                progress.progress(
                    tehtud / koguarv
                )


        status.empty()


        # ====================================================
        # FILTERING
        # ====================================================

        if tulemused:


            df = pd.DataFrame(
                tulemused
            )


            df = df.drop_duplicates(
                subset=["Link"]
            )


            df = df[
                df["Skoor"]
                >=
                min_skoor
            ]


            paevad = (
                perioodi_paevad(
                    periood
                )
            )


            if paevad is not None:


                piir = (
                    datetime.now()
                    -
                    timedelta(
                        days=paevad
                    )
                )


                df = df[
                    df["Kuupäev"]
                    .notna()
                ]


                df = df[
                    df["Kuupäev"]
                    >=
                    piir
                ]


            if ainult_vaikesed:


                if naita_teadmata:


                    df = df[
                        (
                            df[
                                "Vaatamised"
                            ].isna()
                            |
                            (
                                df[
                                    "Vaatamised"
                                ]
                                <=
                                max_vaatamised
                            )
                        )
                        &
                        (
                            df[
                                "Jälgijad"
                            ].isna()
                            |
                            (
                                df[
                                    "Jälgijad"
                                ]
                                <=
                                max_jalgijad
                            )
                        )
                    ]


                else:


                    df = df[
                        df[
                            "Vaatamised"
                        ].notna()
                        &
                        df[
                            "Jälgijad"
                        ].notna()
                    ]


            if peida_juba_salvestatud:

                df = df[
                    ~df["Link"].isin(
                        salvestatud_urlid
                    )
                ]


            if len(df) > 0:

                df[
                    "Väiksuse skoor"
                ] = df.apply(
                    vaiksuse_skoor,
                    axis=1
                )


            # =================================================
            # SORT
            # =================================================

            if sortimine == "Uusimad enne":

                df = df.sort_values(
                    [
                        "Kuupäev",
                        "Skoor"
                    ],
                    ascending=[
                        False,
                        False
                    ],
                    na_position="last"
                )


            elif sortimine == "Kõrgeim Eesti skoor":

                df = df.sort_values(
                    [
                        "Skoor",
                        "Kuupäev"
                    ],
                    ascending=[
                        False,
                        False
                    ],
                    na_position="last"
                )


            elif sortimine == "Kõige vähem vaatamisi":

                df = df.sort_values(
                    [
                        "Vaatamised",
                        "Kuupäev"
                    ],
                    ascending=[
                        True,
                        False
                    ],
                    na_position="last"
                )


            elif sortimine == "Kõige vähem jälgijaid":

                df = df.sort_values(
                    [
                        "Jälgijad",
                        "Kuupäev"
                    ],
                    ascending=[
                        True,
                        False
                    ],
                    na_position="last"
                )


            else:

                df = df.sort_values(
                    [
                        "Väiksuse skoor",
                        "Kuupäev"
                    ],
                    ascending=[
                        False,
                        False
                    ],
                    na_position="last"
                )


            # =================================================
            # RESULTS
            # =================================================

            st.success(
                f"Leidsin "
                f"{len(df)} "
                f"uut tulemust."
            )


            if len(df) == 0:

                st.info(
                    "Valitud filtritega "
                    "tulemusi ei jäänud."
                )


            for nr, (_, row) in enumerate(
                df.iterrows(),
                start=1
            ):


                olemas = (
                    salvestatud_map.get(
                        row["Link"]
                    )
                )


                st.subheader(
                    f"{nr}. "
                    f"{row['Artist']} – "
                    f"{row['Lugu']}"
                )


                col1, col2, col3 = (
                    st.columns(3)
                )


                with col1:

                    st.metric(
                        "🇪🇪 Eesti",
                        f"{int(row['Skoor'])}%"
                    )


                with col2:

                    st.metric(
                        "🌱 Väiksus",
                        f"{int(row['Väiksuse skoor'])}%"
                    )


                with col3:

                    st.write(
                        f"**{row['Platvorm']}**"
                    )


                if pd.notna(
                    row["Kuupäev"]
                ):

                    st.write(
                        "📅",
                        row["Kuupäev"]
                        .strftime(
                            "%d.%m.%Y"
                        )
                    )


                if pd.notna(
                    row["Vaatamised"]
                ):

                    st.write(
                        "👁",
                        vorminda_number(
                            row[
                                "Vaatamised"
                            ]
                        ),
                        "vaatamist"
                    )


                if pd.notna(
                    row["Jälgijad"]
                ):

                    st.write(
                        "👥",
                        vorminda_number(
                            row[
                                "Jälgijad"
                            ]
                        ),
                        "jälgijat"
                    )


                if (
                    row["Platvorm"]
                    ==
                    "Spotify"
                ):

                    st.caption(
                        "Spotify puhul ei ole "
                        "vaatamiste arvu "
                        "YouTube'i kujul saadaval."
                    )


                colA, colB = (
                    st.columns(2)
                )


                with colA:

                    label = (
                        "🟢 Ava Spotifys"
                        if row[
                            "Platvorm"
                        ]
                        ==
                        "Spotify"
                        else
                        "▶ Ava lugu"
                    )


                    st.link_button(
                        label,
                        row["Link"],
                        use_container_width=True
                    )


                with colB:

                    if row["Profiil"]:

                        st.link_button(
                            "👤 Ava artist",
                            row["Profiil"],
                            use_container_width=True
                        )


                with st.expander(
                    "📝 Scouting"
                ):


                    default_status = (
                        olemas.get(
                            "status",
                            "new"
                        )
                        if olemas
                        else
                        "new"
                    )


                    default_note = (
                        olemas.get(
                            "note",
                            ""
                        )
                        if olemas
                        else
                        ""
                    )


                    staatus = (
                        st.selectbox(
                            "Staatus",
                            STATUS_OPTIONS,
                            index=(
                                STATUS_OPTIONS
                                .index(
                                    default_status
                                )
                            ),
                            format_func=lambda x:
                                STATUS_LABELS[x],
                            key=(
                                f"status_"
                                f"{row['Link']}"
                            )
                        )
                    )


                    markus = st.text_area(
                        "Märkus",
                        value=default_note,
                        key=(
                            f"note_"
                            f"{row['Link']}"
                        )
                    )


                    if st.button(
                        "💾 Salvesta",
                        key=(
                            f"save_"
                            f"{row['Link']}"
                        ),
                        use_container_width=True
                    ):


                        ok = salvesta_artist(
                            row["Artist"],
                            row["Platvorm"],
                            row["Lugu"],
                            row["Link"],
                            row["Profiil"],
                            staatus,
                            markus,
                            marked_by
                        )


                        if ok:

                            st.success(
                                "Salvestatud ✅"
                            )

                            st.rerun()


                st.divider()


        else:

            st.warning(
                "Tulemusi ei leitud."
            )