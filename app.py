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
st.write(
    "Otsi uusi Eesti artiste SoundCloudist ja YouTube'ist, "
    "filtreeri väiksemad tegijad ja sorteeri huvitavamad kandidaadid ette."
)


# ============================================================
# OTSINGUD
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
# FILTRID
# ============================================================

st.subheader("⚙️ Otsingu seaded")

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
        min_value=5,
        max_value=30,
        value=10,
        step=5
    )


with col3:

    min_skoor = st.slider(
        "Minimaalne Eesti skoor",
        min_value=0,
        max_value=100,
        value=20,
        step=5
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


# ------------------------------------------------------------
# VÄIKESE ARTISTI FILTRID
# ------------------------------------------------------------

st.subheader("🌱 Väikese artisti filtrid")

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
        "Maksimaalselt jälgijaid / tellijaid",
        min_value=0,
        value=5000,
        step=500
    )


col7, col8, col9 = st.columns(3)

with col7:

    kasuta_vaatamiste_filtrit = st.checkbox(
        "Filtreeri vaatamiste järgi",
        value=False
    )


with col8:

    kasuta_jalgijate_filtrit = st.checkbox(
        "Filtreeri jälgijate järgi",
        value=False
    )


with col9:

    ainult_vaikesed = st.checkbox(
        "🌱 Ainult väikesed artistid",
        value=False,
        help=(
            "Lülitab korraga sisse vaatamiste ja "
            "jälgijate filtrid."
        )
    )


# Kui "ainult väikesed" on sees,
# kasutame mõlemat filtrit.
if ainult_vaikesed:
    kasuta_vaatamiste_filtrit = True
    kasuta_jalgijate_filtrit = True


# ------------------------------------------------------------
# MUUD FILTRID
# ------------------------------------------------------------

col10, col11 = st.columns(2)

with col10:

    naita_teadmata_kuupaeva = st.checkbox(
        "Näita teadmata kuupäevaga tulemusi",
        value=False
    )


with col11:

    naita_teadmata_statistikat = st.checkbox(
        "Näita ka teadmata vaatamiste/jälgijate arvuga tulemusi",
        value=True
    )


# ------------------------------------------------------------
# SORTIMINE
# ------------------------------------------------------------

sortimine = st.selectbox(
    "Sorteeri tulemused",
    [
        "Uusimad enne",
        "Kõrgeim Eesti skoor",
        "Kõige vähem vaatamisi",
        "Kõige vähem jälgijaid",
        "Väikseim artist"
    ]
)


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

        return (
            f"scsearch{arv}:"
        )


    if platvormi_nimi == "YouTube":

        return (
            f"ytsearch{arv}:"
        )


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
# OTSING
# ============================================================

if st.button(
    "🔎 OTSI UUSI EESTI ARTISTE",
    type="primary",
    use_container_width=True
):

    koik_tulemused = []


    ydl_opts = {

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


    otsingute_koguarv = (
        len(otsingud)
        *
        len(kasutatavad_platvormid)
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


                    tulemus = (
                        ydl.extract_info(
                            query,
                            download=False
                        )
                    )


                    if (
                        tulemus
                        and
                        "entries" in tulemus
                    ):


                        for info in tulemus[
                            "entries"
                        ]:


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


                            pealkiri = (

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


                            kestus = (
                                info.get(
                                    "duration"
                                )
                            )


                            vaatamised = (
                                info.get(
                                    "view_count"
                                )
                            )


                            jalgijad = (
                                info.get(
                                    "channel_follower_count"
                                )
                            )


                            profiili_url = (

                                info.get(
                                    "uploader_url"
                                )

                                or

                                info.get(
                                    "channel_url"
                                )

                            )


                            koik_tulemused.append({

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
                                        pohjused
                                    ),

                                "Vaatamised":
                                    vaatamised,

                                "Jälgijad":
                                    jalgijad,

                                "Otsing":
                                    otsing,

                            })


                except Exception as e:


                    st.warning(

                        f"{platvormi_nimi} "

                        f"otsing "

                        f"'{otsing}' "

                        f"andis vea: "

                        f"{e}"

                    )


                tehtud += 1


                progress.progress(

                    tehtud
                    /
                    otsingute_koguarv

                )


    status.empty()


    # ========================================================
    # TULEMUSTE PUHASTAMINE
    # ========================================================

    if koik_tulemused:


        df = pd.DataFrame(
            koik_tulemused
        )


        # Sama URL eemaldame
        df = df.drop_duplicates(
            subset=["Link"]
        )


        # ----------------------------------------------------
        # EESTI SKOOR
        # ----------------------------------------------------

        df = df[
            df["Skoor"]
            >=
            min_skoor
        ]


        # ----------------------------------------------------
        # AJAFILTER
        # ----------------------------------------------------

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


            if naita_teadmata_kuupaeva:


                df = df[

                    (
                        df["Kuupäev"]
                        >=
                        piir
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
                    >=
                    piir

                ]


        elif not naita_teadmata_kuupaeva:


            df = df[

                df["Kuupäev"]
                .notna()

            ]


        # ----------------------------------------------------
        # VAATAMISTE FILTER
        # ----------------------------------------------------

        if kasuta_vaatamiste_filtrit:


            if naita_teadmata_statistikat:


                df = df[

                    df["Vaatamised"]
                    .isna()

                    |

                    (
                        df["Vaatamised"]
                        <=
                        max_vaatamised
                    )

                ]


            else:


                df = df[

                    df["Vaatamised"]
                    .notna()

                ]


                df = df[

                    df["Vaatamised"]
                    <=
                    max_vaatamised

                ]


        # ----------------------------------------------------
        # JÄLGIJATE FILTER
        # ----------------------------------------------------

        if kasuta_jalgijate_filtrit:


            if naita_teadmata_statistikat:


                df = df[

                    df["Jälgijad"]
                    .isna()

                    |

                    (
                        df["Jälgijad"]
                        <=
                        max_jalgijad
                    )

                ]


            else:


                df = df[

                    df["Jälgijad"]
                    .notna()

                ]


                df = df[

                    df["Jälgijad"]
                    <=
                    max_jalgijad

                ]


        # ----------------------------------------------------
        # VÄIKESE ARTISTI SKOOR
        # ----------------------------------------------------

        def vaiksuse_skoor(row):


            score = 0


            vaatamised = row[
                "Vaatamised"
            ]


            jalgijad = row[
                "Jälgijad"
            ]


            if pd.notna(
                vaatamised
            ):

                if vaatamised <= 1000:
                    score += 50

                elif vaatamised <= 5000:
                    score += 40

                elif vaatamised <= 10000:
                    score += 30

                elif vaatamised <= 50000:
                    score += 10


            if pd.notna(
                jalgijad
            ):

                if jalgijad <= 500:
                    score += 50

                elif jalgijad <= 2000:
                    score += 40

                elif jalgijad <= 5000:
                    score += 30

                elif jalgijad <= 10000:
                    score += 10


            return min(
                score,
                100
            )


        if len(df) > 0:

            df["Väiksuse skoor"] = (
                df.apply(
                    vaiksuse_skoor,
                    axis=1
                )
            )


        # ----------------------------------------------------
        # SORTIMINE
        # ----------------------------------------------------

        if sortimine == "Uusimad enne":


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


        elif sortimine == "Kõrgeim Eesti skoor":


            df = df.sort_values(

                by=[
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

                by=[
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

                by=[
                    "Jälgijad",
                    "Kuupäev"
                ],

                ascending=[
                    True,
                    False
                ],

                na_position="last"

            )


        elif sortimine == "Väikseim artist":


            df = df.sort_values(

                by=[
                    "Väiksuse skoor",
                    "Kuupäev"
                ],

                ascending=[
                    False,
                    False
                ],

                na_position="last"

            )


        # ====================================================
        # KOKKUVÕTE
        # ====================================================

        sc_arv = len(

            df[
                df["Platvorm"]
                ==
                "SoundCloud"
            ]

        )


        yt_arv = len(

            df[
                df["Platvorm"]
                ==
                "YouTube"
            ]

        )


        st.success(

            f"🎯 Leidsin "
            f"{len(df)} "
            f"sobivat tulemust"

        )


        col1, col2, col3 = (
            st.columns(3)
        )


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


        # ====================================================
        # CSV EXPORT
        # ====================================================

        if len(df) > 0:


            export_df = df.copy()


            export_df["Kuupäev"] = (
                export_df["Kuupäev"]
                .astype(str)
            )


            csv = (
                export_df.to_csv(
                    index=False
                )
                .encode(
                    "utf-8-sig"
                )
            )


            st.download_button(

                label=(
                    "⬇️ Laadi tulemused CSV failina"
                ),

                data=csv,

                file_name=(
                    "estonian_vocal_radar.csv"
                ),

                mime="text/csv",

                use_container_width=True

            )


        st.divider()


        # ====================================================
        # TULEMUSED
        # ====================================================

        if len(df) == 0:


            st.warning(

                "Tulemusi leiti, kuid "
                "ükski ei läbinud "
                "valitud filtreid."

            )


        else:


            for number, (_, row) in enumerate(
                df.iterrows(),
                start=1
            ):


                colA, colB, colC = (
                    st.columns(
                        [5, 1, 1]
                    )
                )


                with colA:


                    if (
                        row["Platvorm"]
                        ==
                        "YouTube"
                    ):

                        ikoon = "▶️"

                    else:

                        ikoon = "☁️"


                    st.subheader(

                        f"{number}. "
                        f"{ikoon} "
                        f"{row['Artist']} "
                        f"– "
                        f"{row['Lugu']}"

                    )


                with colB:

                    st.metric(

                        "🇪🇪 Eesti",

                        f"{int(row['Skoor'])}%"

                    )


                with colC:

                    st.metric(

                        "🌱 Väiksus",

                        f"{int(row['Väiksuse skoor'])}%"

                    )


                st.write(

                    f"**Platvorm:** "
                    f"{row['Platvorm']}"

                )


                # --------------------------------------------
                # KUUPÄEV
                # --------------------------------------------

                if pd.notna(
                    row["Kuupäev"]
                ):


                    kuupaev = (
                        row["Kuupäev"]
                    )


                    vanus = (

                        datetime.now()

                        -

                        kuupaev

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

                        kuupaev.strftime(
                            "%d.%m.%Y"
                        ),

                        f"— **{vana}**"

                    )


                else:


                    st.write(

                        "📅 Lisamise "
                        "kuupäev teadmata"

                    )


                # --------------------------------------------
                # PIKKUS
                # --------------------------------------------

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


                # --------------------------------------------
                # VAATAMISED
                # --------------------------------------------

                if pd.notna(
                    row["Vaatamised"]
                ):


                    st.write(

                        "👁 Vaatamisi:",

                        vorminda_number(
                            row["Vaatamised"]
                        )

                    )


                else:


                    st.write(

                        "👁 Vaatamiste arv: "
                        "teadmata"

                    )


                # --------------------------------------------
                # JÄLGIJAD
                # --------------------------------------------

                if pd.notna(
                    row["Jälgijad"]
                ):


                    st.write(

                        "👥 Jälgijaid:",

                        vorminda_number(
                            row["Jälgijad"]
                        )

                    )


                else:


                    st.write(

                        "👥 Jälgijate arv: "
                        "teadmata"

                    )


                # --------------------------------------------
                # EESTI SEOSE PÕHJUS
                # --------------------------------------------

                if row["Põhjused"]:


                    st.write(

                        "🇪🇪 Eesti seos:",

                        row["Põhjused"]

                    )


                # --------------------------------------------
                # LINGID
                # --------------------------------------------

                col1, col2 = (
                    st.columns(2)
                )


                with col1:


                    if (
                        row["Platvorm"]
                        ==
                        "YouTube"
                    ):


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

            "SoundCloudist ega "
            "YouTube'ist ei saadud "
            "ühtegi tulemust."

        )