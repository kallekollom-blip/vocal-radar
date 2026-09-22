import streamlit as st
import yt_dlp
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client


# ============================================================
# LEHE SEADED
# ============================================================

st.set_page_config(
    page_title="Estonian Vocal Radar",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Estonian Vocal Radar")
st.caption("SoundCloud + YouTube artistide scouting")


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
# KASUTAJA
# ============================================================

marked_by = st.sidebar.radio(
    "Kes kasutab?",
    ["Kalle", "Vahur"]
)

st.sidebar.write(f"👤 Aktiivne kasutaja: **{marked_by}**")


# ============================================================
# NAVIGATSIOON
# ============================================================

vaade = st.sidebar.radio(
    "Vaade",
    [
        "🔎 Otsi uusi",
        "⭐ Lemmikud",
        "📩 Võta ühendust",
        "👀 Vaadatud",
        "❌ Ei sobi",
        "📋 Kõik salvestatud"
    ]
)


# ============================================================
# ANDMEBAASI FUNKTSIOONID
# ============================================================

def lae_salvestatud():
    try:
        response = (
            supabase
            .table("artists")
            .select("*")
            .execute()
        )

        return response.data or []

    except Exception as e:
        st.error(f"Andmebaasi lugemise viga: {e}")
        return []


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
        olemas = (
            supabase
            .table("artists")
            .select("id")
            .eq("track_url", track_url)
            .execute()
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

        if olemas.data:

            artist_id = olemas.data[0]["id"]

            (
                supabase
                .table("artists")
                .update(data)
                .eq("id", artist_id)
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


# ============================================================
# OTSINGU SEADED
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
    "Tartu vocalist",
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
# ABIFUNKTSIOONID
# ============================================================

def saa_kuupaev(info):

    timestamp = info.get("timestamp")

    if timestamp:

        try:
            return datetime.fromtimestamp(timestamp)

        except:
            pass


    upload_date = info.get("upload_date")

    if upload_date:

        try:
            return datetime.strptime(
                upload_date,
                "%Y%m%d"
            )

        except:
            pass


    release_timestamp = info.get(
        "release_timestamp"
    )

    if release_timestamp:

        try:
            return datetime.fromtimestamp(
                release_timestamp
            )

        except:
            pass


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

    skoor = 0
    pohjused = []

    juba_leitud = set()

    for sona, punktid in eesti_marksonad.items():

        if sona in tekst and sona not in juba_leitud:

            skoor += punktid

            juba_leitud.add(
                sona
            )

            pohjused.append(
                sona
            )


    if otsing.lower() in tekst:
        skoor += 10


    return min(skoor, 100), pohjused


def platvormid_otsimiseks(valik):

    if valik == "SoundCloud":
        return ["SoundCloud"]

    if valik == "YouTube":
        return ["YouTube"]

    return [
        "SoundCloud",
        "YouTube"
    ]


def otsingu_prefix(
    platvormi_nimi,
    arv
):

    if platvormi_nimi == "SoundCloud":
        return f"scsearch{arv}:"

    if platvormi_nimi == "YouTube":
        return f"ytsearch{arv}:"

    return ""


def vorminda_number(number):

    try:

        number = int(number)

        if number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"

        if number >= 1000:
            return f"{number / 1000:.1f}K"

        return str(number)

    except:

        return "?"


# ============================================================
# SALVESTATUD ARTISTIDE VAATED
# ============================================================

if vaade != "🔎 Otsi uusi":

    st.subheader(vaade)

    salvestatud = lae_salvestatud()

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
            x for x in salvestatud
            if x.get("status") == soovitud_status
        ]


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

        st.write(
            f"**Staatus:** "
            f"{artist.get('status', '')}"
        )

        st.write(
            f"**Märkis:** "
            f"{artist.get('marked_by', '')}"
        )


        note = artist.get(
            "note"
        )

        if note:

            st.info(
                f"📝 {note}"
            )


        col1, col2 = st.columns(2)

        with col1:

            if artist.get("track_url"):

                st.link_button(
                    "▶ Ava lugu",
                    artist["track_url"],
                    use_container_width=True
                )


        with col2:

            if artist.get("profile_url"):

                st.link_button(
                    "👤 Ava artist",
                    artist["profile_url"],
                    use_container_width=True
                )


        st.divider()


# ============================================================
# OTSING
# ============================================================

else:

    st.subheader("🔎 Otsi uusi artiste")


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        platvorm = st.selectbox(
            "Platvorm",
            [
                "Mõlemad",
                "SoundCloud",
                "YouTube"
            ]
        )


    with col2:

        tulemusi_otsingu_kohta = st.slider(
            "Tulemusi iga otsingu kohta",
            5,
            30,
            10,
            5
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


    # --------------------------------------------------------
    # VÄIKESE ARTISTI FILTRID
    # --------------------------------------------------------

    st.write("### 🌱 Väikese artisti filtrid")


    col5, col6 = st.columns(2)


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


    # ========================================================
    # SEARCH BUTTON
    # ========================================================

    if st.button(
        "🔎 OTSI",
        type="primary",
        use_container_width=True
    ):

        tulemused = []


        opts = {
            "extract_flat": False,
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ignoreerrors": True,
        }


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

        progress = st.progress(0)

        status = st.empty()


        with yt_dlp.YoutubeDL(
            opts
        ) as ydl:


            for platvormi_nimi in kasutatavad_platvormid:


                for otsing in otsingud:


                    status.write(
                        f"🔎 {platvormi_nimi}: "
                        f"**{otsing}**"
                    )


                    try:

                        query = (
                            otsingu_prefix(
                                platvormi_nimi,
                                tulemusi_otsingu_kohta
                            )
                            +
                            otsing
                        )


                        tulemus = ydl.extract_info(
                            query,
                            download=False
                        )


                        if tulemus and "entries" in tulemus:


                            for info in tulemus["entries"]:


                                if not info:
                                    continue


                                url = (
                                    info.get("webpage_url")
                                    or
                                    info.get("original_url")
                                    or
                                    info.get("url")
                                )


                                if not url:
                                    continue


                                artist = (
                                    info.get("uploader")
                                    or
                                    info.get("channel")
                                    or
                                    "Tundmatu artist"
                                )


                                title = (
                                    info.get("title")
                                    or
                                    "Pealkiri puudub"
                                )


                                kuupaev = saa_kuupaev(
                                    info
                                )


                                skoor, pohjused = arvuta_skoor(
                                    info,
                                    otsing
                                )


                                tulemused.append({

                                    "Platvorm":
                                        platvormi_nimi,

                                    "Artist":
                                        artist,

                                    "Lugu":
                                        title,

                                    "Link":
                                        url,

                                    "Profiil":
                                        (
                                            info.get("uploader_url")
                                            or
                                            info.get("channel_url")
                                        ),

                                    "Kuupäev":
                                        kuupaev,

                                    "Pikkus":
                                        info.get("duration"),

                                    "Skoor":
                                        skoor,

                                    "Põhjused":
                                        ", ".join(pohjused),

                                    "Vaatamised":
                                        info.get("view_count"),

                                    "Jälgijad":
                                        info.get(
                                            "channel_follower_count"
                                        ),

                                })


                    except Exception as e:

                        st.warning(
                            f"{platvormi_nimi}: "
                            f"{otsing}: {e}"
                        )


                    tehtud += 1

                    progress.progress(
                        tehtud / koguarv
                    )


        status.empty()


        # ====================================================
        # DATAFRAME
        # ====================================================

        if tulemused:


            df = pd.DataFrame(
                tulemused
            )


            df = df.drop_duplicates(
                subset=["Link"]
            )


            df = df[
                df["Skoor"] >= min_skoor
            ]


            # ------------------------------------------------
            # AJAFILTER
            # ------------------------------------------------

            paevad = perioodi_paevad(
                periood
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
                    df["Kuupäev"].notna()
                ]


                df = df[
                    df["Kuupäev"] >= piir
                ]


            # ------------------------------------------------
            # VÄIKESE ARTISTI FILTER
            # ------------------------------------------------

            if ainult_vaikesed:


                if naita_teadmata:


                    df = df[
                        (
                            df["Vaatamised"].isna()
                            |
                            (
                                df["Vaatamised"]
                                <=
                                max_vaatamised
                            )
                        )
                        &
                        (
                            df["Jälgijad"].isna()
                            |
                            (
                                df["Jälgijad"]
                                <=
                                max_jalgijad
                            )
                        )
                    ]


                else:


                    df = df[
                        df["Vaatamised"].notna()
                        &
                        df["Jälgijad"].notna()
                    ]


                    df = df[
                        (
                            df["Vaatamised"]
                            <=
                            max_vaatamised
                        )
                        &
                        (
                            df["Jälgijad"]
                            <=
                            max_jalgijad
                        )
                    ]


            # ------------------------------------------------
            # VÄIKSUSE SKOOR
            # ------------------------------------------------

            def vaiksuse_skoor(row):

                score = 0

                views = row["Vaatamised"]
                followers = row["Jälgijad"]


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


            if len(df) > 0:

                df["Väiksuse skoor"] = df.apply(
                    vaiksuse_skoor,
                    axis=1
                )


            # ------------------------------------------------
            # SORT
            # ------------------------------------------------

            if sortimine == "Uusimad enne":

                df = df.sort_values(
                    ["Kuupäev", "Skoor"],
                    ascending=[False, False],
                    na_position="last"
                )


            elif sortimine == "Kõrgeim Eesti skoor":

                df = df.sort_values(
                    ["Skoor", "Kuupäev"],
                    ascending=[False, False],
                    na_position="last"
                )


            elif sortimine == "Kõige vähem vaatamisi":

                df = df.sort_values(
                    ["Vaatamised", "Kuupäev"],
                    ascending=[True, False],
                    na_position="last"
                )


            elif sortimine == "Kõige vähem jälgijaid":

                df = df.sort_values(
                    ["Jälgijad", "Kuupäev"],
                    ascending=[True, False],
                    na_position="last"
                )


            else:

                df = df.sort_values(
                    ["Väiksuse skoor", "Kuupäev"],
                    ascending=[False, False],
                    na_position="last"
                )


            # =================================================
            # TULEMUSED
            # =================================================

            st.success(
                f"Leidsin {len(df)} tulemust."
            )


            if len(df) == 0:

                st.info(
                    "Valitud filtritega tulemusi ei jäänud."
                )


            for nr, (_, row) in enumerate(
                df.iterrows(),
                start=1
            ):


                st.subheader(
                    f"{nr}. "
                    f"{row['Artist']} – "
                    f"{row['Lugu']}"
                )


                col1, col2, col3 = st.columns(3)


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


                if pd.notna(row["Kuupäev"]):

                    st.write(
                        "📅",
                        row["Kuupäev"].strftime(
                            "%d.%m.%Y"
                        )
                    )


                if pd.notna(row["Vaatamised"]):

                    st.write(
                        "👁",
                        vorminda_number(
                            row["Vaatamised"]
                        ),
                        "vaatamist"
                    )


                if pd.notna(row["Jälgijad"]):

                    st.write(
                        "👥",
                        vorminda_number(
                            row["Jälgijad"]
                        ),
                        "jälgijat"
                    )


                colA, colB = st.columns(2)


                with colA:

                    st.link_button(
                        "▶ Ava lugu",
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


                # =============================================
                # SCOUTING
                # =============================================

                with st.expander(
                    "📝 Scouting"
                ):


                    staatus = st.selectbox(
                        "Staatus",
                        [
                            "new",
                            "favorite",
                            "seen",
                            "contact",
                            "reject"
                        ],
                        format_func=lambda x: {
                            "new": "🆕 Uus",
                            "favorite": "⭐ Lemmik",
                            "seen": "👀 Vaadatud",
                            "contact": "📩 Võta ühendust",
                            "reject": "❌ Ei sobi"
                        }[x],
                        key=f"status_{nr}"
                    )


                    markus = st.text_area(
                        "Märkus",
                        key=f"note_{nr}",
                        placeholder=(
                            "Näiteks: hea vokaal, "
                            "sobib DnB refrääni..."
                        )
                    )


                    if st.button(
                        "💾 Salvesta",
                        key=f"save_{nr}",
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


                st.divider()


        else:

            st.warning(
                "Tulemusi ei leitud."
            )