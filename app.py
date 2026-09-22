import streamlit as st
import yt_dlp
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Estonian Vocal Radar",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Estonian Vocal Radar")
st.write("Otsi uusi Eesti artiste SoundCloudist ja YouTube'ist")


# ------------------------------------------------
# OTSINGUD
# ------------------------------------------------

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
    "Estonian music",
    "Estonian vocalist",
    "Eesti laulja",
    "Eesti muusika",
    "Eesti cover",
    "Eesti demo",
    "Tallinn singer",
    "Tartu singer",
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


# ------------------------------------------------
# FILTRID
# ------------------------------------------------

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
        "Kui uusi lugusid näidata?",
        [
            "Viimased 7 päeva",
            "Viimased 30 päeva",
            "Viimased 90 päeva",
            "Viimased 365 päeva",
            "Kõik"
        ],
        index=1
    )


naita_teadmata = st.checkbox(
    "Näita ka lugusid/videoid, mille kuupäev pole teada",
    value=False
)


# ------------------------------------------------
# ABIFUNKTSIOONID
# ------------------------------------------------

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

    release_timestamp = info.get("release_timestamp")

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
    põhjused = []

    juba_leitud = set()

    for sona, punktid in eesti_marksonad.items():

        if sona in tekst and sona not in juba_leitud:

            skoor += punktid
            juba_leitud.add(sona)

            põhjused.append(
                sona
            )

    # Kui otsingu täpne fraas esineb metadata sees,
    # anname väikese lisaboonuse.
    if otsing.lower() in tekst:
        skoor += 10

    return min(skoor, 100), põhjused


def platvormid_otsimiseks(valik):

    if valik == "SoundCloud":
        return ["SoundCloud"]

    if valik == "YouTube":
        return ["YouTube"]

    return [
        "SoundCloud",
        "YouTube"
    ]


def otsingu_prefix(platvormi_nimi, arv):

    if platvormi_nimi == "SoundCloud":
        return f"scsearch{arv}:"

    if platvormi_nimi == "YouTube":
        return f"ytsearch{arv}:"

    return ""


# ------------------------------------------------
# OTSING
# ------------------------------------------------

if st.button(
    "🔎 OTSI UUSI EESTI ARTISTE",
    type="primary",
    use_container_width=True
):

    kõik_tulemused = []

    ydl_opts = {
        "extract_flat": False,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
    }

    kasutatavad_platvormid = platvormid_otsimiseks(
        platvorm
    )

    otsingute_koguarv = (
        len(otsingud)
        * len(kasutatavad_platvormid)
    )

    tehtud = 0

    progress = st.progress(0)
    status = st.empty()

    with yt_dlp.YoutubeDL(
        ydl_opts
    ) as ydl:

        for platvormi_nimi in kasutatavad_platvormid:

            for otsing in otsingud:

                status.write(
                    f"🔎 {platvormi_nimi}: **{otsing}**"
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
                                or info.get("original_url")
                                or info.get("url")
                            )

                            if not url:
                                continue

                            artist = (
                                info.get("uploader")
                                or info.get("channel")
                                or "Tundmatu artist"
                            )

                            pealkiri = (
                                info.get("title")
                                or "Pealkiri puudub"
                            )

                            kuupaev = saa_kuupaev(
                                info
                            )

                            skoor, põhjused = arvuta_skoor(
                                info,
                                otsing
                            )

                            kestus = info.get(
                                "duration"
                            )

                            vaatamised = info.get(
                                "view_count"
                            )

                            jälgijad = info.get(
                                "channel_follower_count"
                            )

                            profiili_url = (
                                info.get("uploader_url")
                                or info.get("channel_url")
                            )

                            kõik_tulemused.append({

                                "Platvorm":
                                    platvormi_nimi,

                                "Artist":
                                    artist,

                                "Lugu":
                                    pealkiri,

                                "Link":
                                    url,

                                "Profiil":
                                    profiili_url,

                                "Kuupäev":
                                    kuupaev,

                                "Pikkus":
                                    kestus,

                                "Skoor":
                                    skoor,

                                "Põhjused":
                                    ", ".join(
                                        põhjused
                                    ),

                                "Vaatamised":
                                    vaatamised,

                                "Jälgijad":
                                    jälgijad,

                                "Otsing":
                                    otsing,
                            })

                except Exception as e:

                    st.warning(
                        f"{platvormi_nimi} otsing "
                        f"'{otsing}' andis vea: {e}"
                    )

                tehtud += 1

                progress.progress(
                    tehtud
                    / otsingute_koguarv
                )

    status.empty()


    # ------------------------------------------------
    # TULEMUSTE PUHASTAMINE
    # ------------------------------------------------

    if kõik_tulemused:

        df = pd.DataFrame(
            kõik_tulemused
        )

        # Sama URL ainult üks kord
        df = df.drop_duplicates(
            subset=["Link"]
        )

        # Eesti skoori filter
        df = df[
            df["Skoor"] >= min_skoor
        ]


        # ------------------------------------------------
        # AJAFILTER
        # ------------------------------------------------

        päevad = perioodi_paevad(
            periood
        )

        if päevad is not None:

            piir = (
                datetime.now()
                -
                timedelta(
                    days=päevad
                )
            )

            if naita_teadmata:

                df = df[
                    (
                        df["Kuupäev"]
                        >= piir
                    )
                    |
                    (
                        df["Kuupäev"]
                        .isna()
                    )
                ]

            else:

                df = df[
                    df["Kuupäev"]
                    .notna()
                ]

                df = df[
                    df["Kuupäev"]
                    >= piir
                ]

        elif not naita_teadmata:

            df = df[
                df["Kuupäev"]
                .notna()
            ]


        # ------------------------------------------------
        # SORTEERIMINE
        # ------------------------------------------------

        df = df.sort_values(
            by=[
                "Kuupäev",
                "Skoor"
            ],
            ascending=[
                False,
                False
            ],
            na_position="last"
        )


        # ------------------------------------------------
        # KOKKUVÕTE
        # ------------------------------------------------

        sc_arv = len(
            df[
                df["Platvorm"]
                == "SoundCloud"
            ]
        )

        yt_arv = len(
            df[
                df["Platvorm"]
                == "YouTube"
            ]
        )

        st.success(
            f"🎯 Leidsin {len(df)} sobivat tulemust"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Kokku",
                len(df)
            )

        with col2:
            st.metric(
                "☁️ SoundCloud",
                sc_arv
            )

        with col3:
            st.metric(
                "▶️ YouTube",
                yt_arv
            )

        st.divider()


        # ------------------------------------------------
        # TULEMUSTE NÄITAMINE
        # ------------------------------------------------

        if len(df) == 0:

            st.warning(
                "Tulemusi leiti, kuid ükski ei läbinud filtreid."
            )

        else:

            for number, (_, row) in enumerate(
                df.iterrows(),
                start=1
            ):

                colA, colB = st.columns(
                    [5, 1]
                )

                with colA:

                    if row["Platvorm"] == "YouTube":
                        ikoon = "▶️"
                    else:
                        ikoon = "☁️"

                    st.subheader(
                        f"{number}. {ikoon} "
                        f"{row['Artist']} – "
                        f"{row['Lugu']}"
                    )

                with colB:

                    st.metric(
                        "🇪🇪 Eesti skoor",
                        f"{int(row['Skoor'])}%"
                    )


                st.write(
                    f"**Platvorm:** "
                    f"{row['Platvorm']}"
                )


                # KUUPÄEV

                if pd.notna(
                    row["Kuupäev"]
                ):

                    kuupäev = row[
                        "Kuupäev"
                    ]

                    vanus = (
                        datetime.now()
                        -
                        kuupäev
                    ).days

                    if vanus == 0:
                        vana = "Täna"

                    elif vanus == 1:
                        vana = "Eile"

                    else:
                        vana = (
                            f"{vanus} päeva tagasi"
                        )

                    st.write(
                        "📅 Lisatud:",
                        kuupäev.strftime(
                            "%d.%m.%Y"
                        ),
                        f"— **{vana}**"
                    )

                else:

                    st.write(
                        "📅 Lisamise kuupäev teadmata"
                    )


                # PIKKUS

                if row["Pikkus"]:

                    try:

                        sekundid = int(
                            row["Pikkus"]
                        )

                        st.write(
                            f"⏱ "
                            f"{sekundid // 60}:"
                            f"{sekundid % 60:02d}"
                        )

                    except:
                        pass


                # VAATAMISED

                if pd.notna(
                    row["Vaatamised"]
                ):

                    try:

                        st.write(
                            "👁 Vaatamisi:",
                            f"{int(row['Vaatamised']):,}"
                        )

                    except:
                        pass


                # JÄLGIJAD

                if pd.notna(
                    row["Jälgijad"]
                ):

                    try:

                        st.write(
                            "👥 Jälgijaid:",
                            f"{int(row['Jälgijad']):,}"
                        )

                    except:
                        pass


                if row["Põhjused"]:

                    st.write(
                        "🇪🇪 Eesti seos:",
                        row["Põhjused"]
                    )


                # LINGID

                col1, col2 = st.columns(2)

                with col1:

                    if row["Platvorm"] == "YouTube":

                        st.link_button(
                            "▶️ Vaata YouTube'is",
                            row["Link"],
                            use_container_width=True
                        )

                    else:

                        st.link_button(
                            "☁️ Kuula SoundCloudis",
                            row["Link"],
                            use_container_width=True
                        )

                with col2:

                    if row["Profiil"]:

                        st.link_button(
                            "👤 Ava artist",
                            row["Profiil"],
                            use_container_width=True
                        )

                st.caption(
                    f"Leitud otsinguga: "
                    f"{row['Otsing']}"
                )

                st.divider()

    else:

        st.error(
            "SoundCloudist ega YouTube'ist "
            "ei saadud ühtegi tulemust."
        )