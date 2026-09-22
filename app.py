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
st.write("SoundCloudi uute Eesti artistide ja vokalistide radar")


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
    "Eesti laul",
    "Eesti muusika",
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

col1, col2, col3 = st.columns(3)

with col1:
    tulemusi_otsingu_kohta = st.slider(
        "Tulemusi iga otsingu kohta",
        5,
        30,
        10,
        5
    )

with col2:
    min_skoor = st.slider(
        "Minimaalne Eesti skoor",
        0,
        100,
        20,
        5
    )

with col3:
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


kontrolli_profiili = st.checkbox(
    "🔍 Kontrolli artisti SoundCloudi profiili",
    value=False
)

naita_teadmata = st.checkbox(
    "Näita ka lugusid, mille kuupäev pole teada",
    value=False
)


# ------------------------------------------------
# ABIFUNKTSIOONID
# ------------------------------------------------

def saa_kuupaev(lugu):

    timestamp = lugu.get("timestamp")

    if timestamp:
        try:
            return datetime.fromtimestamp(timestamp)
        except:
            pass

    upload_date = lugu.get("upload_date")

    if upload_date:
        try:
            return datetime.strptime(
                upload_date,
                "%Y%m%d"
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


# ------------------------------------------------
# LOO SKOOR
# ------------------------------------------------

def arvuta_skoor(lugu, otsing):

    tekst = " ".join([
        str(lugu.get("title", "")),
        str(lugu.get("uploader", "")),
        str(lugu.get("description", "")),
        str(lugu.get("genre", "")),
        str(lugu.get("tags", "")),
        str(otsing)
    ]).lower()

    skoor = 0
    põhjused = []

    juba_leitud = set()

    for sona, punktid in eesti_marksonad.items():

        if sona in tekst and sona not in juba_leitud:

            skoor += punktid
            juba_leitud.add(sona)

            põhjused.append(
                f"Leitud märksõna: {sona}"
            )

    return min(skoor, 100), põhjused


# ------------------------------------------------
# PROFIILI KONTROLL
# ------------------------------------------------

@st.cache_data(ttl=3600)
def kontrolli_artisti_profiili(profiili_url):

    if not profiili_url:
        return 0, [], ""

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": 1,
    }

    try:

        with yt_dlp.YoutubeDL(opts) as ydl:

            info = ydl.extract_info(
                profiili_url,
                download=False
            )

        if not info:
            return 0, [], ""

        tekst = " ".join([
            str(info.get("title", "")),
            str(info.get("uploader", "")),
            str(info.get("description", "")),
            str(info.get("location", "")),
        ]).lower()

        skoor = 0
        põhjused = []

        for sona in eesti_marksonad:

            if sona in tekst:
                skoor += 40
                põhjused.append(
                    f"Profiil: {sona}"
                )

        skoor = min(skoor, 100)

        bio = str(
            info.get("description", "")
        )

        return skoor, põhjused, bio

    except Exception:
        return 0, [], ""


# ------------------------------------------------
# OTSING
# ------------------------------------------------

if st.button(
    "🔎 OTSI UUSI EESTI ARTISTE",
    type="primary",
    use_container_width=True
):

    kõik_lood = []

    ydl_opts = {
        "extract_flat": False,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    progress = st.progress(0)

    status = st.empty()

    with yt_dlp.YoutubeDL(
        ydl_opts
    ) as ydl:

        for nr, otsing in enumerate(
            otsingud
        ):

            status.write(
                f"🔎 Otsin: **{otsing}**"
            )

            try:

                tulemus = ydl.extract_info(
                    f"scsearch{tulemusi_otsingu_kohta}:{otsing}",
                    download=False
                )

                if tulemus and "entries" in tulemus:

                    for lugu in tulemus["entries"]:

                        if not lugu:
                            continue

                        url = (
                            lugu.get("webpage_url")
                            or lugu.get("url")
                        )

                        if not url:
                            continue

                        artist = (
                            lugu.get("uploader")
                            or "Tundmatu artist"
                        )

                        profiili_url = (
                            lugu.get("uploader_url")
                            or lugu.get("channel_url")
                        )

                        kuupaev = saa_kuupaev(
                            lugu
                        )

                        loo_skoor, põhjused = arvuta_skoor(
                            lugu,
                            otsing
                        )

                        profiili_skoor = 0
                        profiili_põhjused = []
                        profiili_bio = ""

                        # Profiilikontroll ei tohi põhiotsingut katkestada
                        if kontrolli_profiili and profiili_url:

                            try:
                                (
                                    profiili_skoor,
                                    profiili_põhjused,
                                    profiili_bio
                                ) = kontrolli_artisti_profiili(
                                    profiili_url
                                )

                            except Exception:
                                profiili_skoor = 0
                                profiili_põhjused = []
                                profiili_bio = ""

                        lõplik_skoor = min(
                            100,
                            loo_skoor + profiili_skoor
                        )

                        kõik_põhjused = (
                            põhjused
                            + profiili_põhjused
                        )

                        kõik_lood.append({

                            "Artist":
                                artist,

                            "Lugu":
                                lugu.get(
                                    "title",
                                    "Pealkiri puudub"
                                ),

                            "Link":
                                url,

                            "Profiil":
                                profiili_url,

                            "Kuupäev":
                                kuupaev,

                            "Pikkus":
                                lugu.get(
                                    "duration"
                                ),

                            "Skoor":
                                lõplik_skoor,

                            "Põhjused":
                                ", ".join(
                                    kõik_põhjused
                                ),

                            "Bio":
                                profiili_bio,

                            "Otsing":
                                otsing,
                        })

            except Exception as e:

                st.warning(
                    f"Otsing '{otsing}' andis vea: {e}"
                )

            progress.progress(
                (nr + 1)
                / len(otsingud)
            )

    status.empty()


    # ------------------------------------------------
    # TULEMUSTE PUHASTAMINE
    # ------------------------------------------------

    if kõik_lood:

        df = pd.DataFrame(
            kõik_lood
        )

        df = df.drop_duplicates(
            subset=["Link"]
        )

        # Eesti skoori filter
        df = df[
            df["Skoor"]
            >= min_skoor
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
        # TULEMUSED
        # ------------------------------------------------

        st.success(
            f"🎯 Leidsin {len(df)} sobivat tulemust"
        )

        st.write(
            f"Periood: **{periood}** • "
            f"Minimaalne Eesti skoor: **{min_skoor}%**"
        )

        st.divider()

        if len(df) == 0:

            st.warning(
                "Tulemused leiti, kuid ükski ei läbinud valitud filtreid. "
                "Proovi Eesti skoor 0 ja periood Kõik."
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

                    st.subheader(
                        f"{number}. "
                        f"{row['Artist']} – "
                        f"{row['Lugu']}"
                    )

                with colB:

                    st.metric(
                        "🇪🇪 Eesti skoor",
                        f"{int(row['Skoor'])}%"
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


                # EESTI SEOSE PÕHJUS

                if row["Põhjused"]:

                    st.write(
                        "🇪🇪 **Eesti seose põhjus:**",
                        row["Põhjused"]
                    )


                # BIO

                if row["Bio"]:

                    with st.expander(
                        "👤 Artisti profiili info"
                    ):

                        st.write(
                            row["Bio"][:1000]
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


                # LINGID

                col1, col2 = st.columns(2)

                with col1:

                    st.link_button(
                        "▶ Kuula lugu",
                        row["Link"]
                    )

                with col2:

                    if row["Profiil"]:

                        st.link_button(
                            "👤 Ava artist",
                            row["Profiil"]
                        )

                st.caption(
                    f"Leitud otsinguga: "
                    f"{row['Otsing']}"
                )

                st.divider()

    else:

        st.error(
            "SoundCloudist ei saadud ühtegi tulemust. "
            "Vaata ülal olevaid veateateid."
        )