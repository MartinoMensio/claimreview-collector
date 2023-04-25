from claimreview_collector.processing import claimreview

# textual label
cr_1 = {
    "itemReviewed": {
        "@type": "CreativeWork",
        "url": "https://www.facebook.com/zoilocnieto/posts/3638208249543989",
        "datePublished": "2020-10-04",
        "keywords": "factchat",
        "author": {"@type": "Person", "name": "Fuentes Varias"},
    },
    "author": {
        "@type": "Organization",
        "@id": "https://factual.afp.com/",
        "name": "Factual",
        "url": "https://factual.afp.com/",
        "sameAs": "https://twitter.com/AFPFactual",
        "logo": {
            "@type": "ImageObject",
            "url": "https://factuel.afp.com/sites/all/themes/custom/afpblog/v2/assets/img/Logo_AFP.svg",
            "width": "",
            "height": "",
        },
    },
    "reviewRating": {
        "@type": "Rating",
        "ratingValue": "5",
        "bestRating": "1",
        "worstRating": "5",
        "alternateName": "Falso",
    },
    "claimReviewed": "Motociclistas se arrodillaron y oraron por la salud de Donald Trump",
    "@type": "ClaimReview",
    "name": "Los motociclistas ped\u00edan que cese la violencia contra granjeros en Sud\u00e1frica, no por Donald Trump",
    "datePublished": "2020-10-07 20:05",
    "url": "https://factual.afp.com/los-motociclistas-pedian-que-cese-la-violencia-contra-granjeros-en-sudafrica-no-por-donald-trump",
}

# numeric label
cr_2 = {
    "itemReviewed": {
        "@type": "CreativeWork",
        "@id": "",
        "name": "",
        "url": "",
        "datePublished": "",
        "author": {
            "@type": "Person",
            "name": "Fuentes m\u00faltiples",
            "url": "https://www.facebook.com/viviann.williams.1/posts/2168907433130951",
            "sameAs": "",
        },
    },
    "author": {
        "@type": "Organization",
        "@id": "https://factual.afp.com/",
        "name": "Factual",
        "url": "https://factual.afp.com/",
        "sameAs": "https://twitter.com/AfpFactual",
        "logo": {
            "@type": "ImageObject",
            "url": "https://factuel.afp.com/sites/all/themes/custom/afpblog/v2/assets/img/Logo_AFP.svg",
            "width": "",
            "height": "",
        },
    },
    "reviewRating": {
        "@type": "Rating",
        "ratingValue": "3",
        "bestRating": "5",
        "worstRating": "1",
        "alternateName": "Mixto",
    },
    "claimReviewed": "Fotos tomadas despu\u00e9s del tornado en La Habana, Cuba, en 2019",
    "@type": "ClaimReview",
    "name": "No, no todas estas fotograf\u00edas muestran el impacto del \u00faltimo tornado en La Habana",
    "datePublished": "2019-02-21 23:12",
    "url": "https://factual.afp.com/no-no-todas-estas-fotografias-muestran-el-impacto-del-ultimo-tornado-en-la-habana",
}

# difficult to map
cr_3 = {
    "@context": "http://schema.org",
    "@type": "ClaimReview",
    "datePublished": "2017-03-01 20:30:17 UTC",
    "url": "http://www.politifact.com/article/2017/mar/01/did-trump-inherit-mess-8-charts-show-otherwise/",
    "author": {"@type": "Organization", "url": "https://www.politifact.com"},
    "claimReviewed": "Did Donald Trump inherit an economic mess? ",
    "reviewRating": {
        "@type": "Rating",
        "ratingValue": "-1",
        "alternateName": "Not really, charts say",
        "worstRating": "-1",
        "bestRating": "-1",
        "image": "https://dhpikd1t89arn.cloudfront.net/custom-rating/custom-ratings-33203093-6cb9-41bc-a56f-71e895db93fe",
    },
    "itemReviewed": {
        "@type": "CreativeWork",
        "author": {
            "@type": "Person",
            "name": "Donald Trump",
            "jobTitle": "President",
            "image": "https://dhpikd1t89arn.cloudfront.net/custom-rating/custom-ratings-33203093-6cb9-41bc-a56f-71e895db93fe",
            "sameAs": [],
        },
        "datePublished": "2017-02-28",
        "name": "an address to Congress",
    },
}

# firstAppearance
cr_4 = {
    "@context": "https://schema.org",
    "@type": "ClaimReview",
    "datePublished": "2020-03-10T12:31:20+01:00",
    "author": {
        "@type": "Organization",
        "name": "Le Monde",
        "url": "https://www.lemonde.fr/",
    },
    "url": "https://www.lemonde.fr/les-decodeurs/article/2020/03/10/coronavirus-peut-on-vraiment-dire-que-le-covid-19-n-est-qu-un-gros-rhume-monte-en-epingle_6032483_4355770.html",
    "claimReviewed": "Le coronavirus n\u2019est qu\u2019un\u00a0\u00ab gros rhume mont\u00e9 en \u00e9pingle\u00a0\u00bb",
    "itemReviewed": {
        "@type": "Claim",
        "author": {"@type": "Person", "name": "Plusieurs sites internet"},
        "datePublished": "2020-02-03T00:00:00+00:00",
        "appearance": [
            {
                "@type": "CreativeWork",
                "url": "https://drschmitz.lettre-medecin-sante.com/coronavirus-lepidemie-est-ailleurs/",
            }
        ],
    },
    "reviewRating": {
        "@type": "Rating",
        "ratingValue": "1",
        "bestRating": "2",
        "worstRating": "0",
        "alternateName": "C\u2019est plus compliqu\u00e9",
    },
    "retrieved_by": "poynter_covid",
}

cr_5 = {
    "@context": "http://schema.org",
    "@type": "ClaimReview",
    "url": "https://www.lemonde.fr/les-decodeurs/article/2017/02/27/des-militants-denoncent-l-omerta-des-medias-sur-l-agression-d-un-pretre-a-avignon-qui-date-de-2013_5086287_4355770.html",
    "author": {
        "@type": "Organization",
        "name": "Le Monde",
        "url": "https://www.lemonde.fr",
        "logo": "https://asset.lemde.fr/medias/img/social-network/default.png",
        "sameAs": [
            "https://www.facebook.com/lemonde.fr",
            "https://twitter.com/lemondefr",
            "https://www.instagram.com/lemondefr/",
            "https://www.youtube.com/user/LeMonde",
            "https://www.linkedin.com/company/le-monde/",
        ],
    },
    "claimReviewed": "",
    "reviewRating": {
        "@type": "Rating",
        "ratingValue": 0,
        "bestRating": 2,
        "worstRating": 0,
        "alternateName": "FAUX",
    },
    "itemReviewed": {
        "@type": "Claim",
        "appearance": [
            {
                "@type": "CreativeWork",
                "url": "https://www.facebook.com/CorentinFNJ/posts/250959068694828",
            },
            {
                "@type": "CreativeWork",
                "url": "http://www.paulomouvementcitoyen.com/2017/02/un-pretre-agresse-a-avignon.html",
            },
            {
                "@type": "CreativeWork",
                "url": "https://www.blog.sami-aldeeb.com/2017/02/06/pretre-agresse-a-avignon-si-ca-avait-ete-un-imam/",
            },
            {
                "@type": "CreativeWork",
                "url": "https://francaisdefrance.wordpress.com/2016/12/12/agression-dun-moine-hier-soir-silence-total-heureusement-il-y-a-internet/",
            },
            {
                "@type": "CreativeWork",
                "url": "https://www.facebook.com/10212204315883498/posts/10212140163199721",
            },
            {
                "@type": "CreativeWork",
                "url": "https://www.facebook.com/387841388254774/posts/383701835335396",
            },
            {
                "@type": "CreativeWork",
                "url": "https://twitter.com/MONSTERLOVE696/status/976170425272160258",
            },
        ],
    },
    "origin": "lemonde_decodex_hoax",
    "retrieved_by": "lemonde_decodex_hoax",
}

shortened_cr_url = "https://bit.ly/claimreview-example"


def test_get_numeric_rating():
    assert claimreview.get_numeric_rating(cr_1) == 0
    assert claimreview.get_numeric_rating(cr_2) == 0.5
    assert claimreview.get_numeric_rating(cr_3) == None


def test_get_coinform_label():
    assert claimreview.get_coinform_label(cr_1) == "not_credible"
    assert claimreview.get_coinform_label(cr_2) == "uncertain"
    assert claimreview.get_coinform_label(cr_3) == "not_verifiable"


def test_get_coinform_label_from_score():
    assert claimreview.get_coinform_label_from_score(0.9) == "credible"
    assert claimreview.get_coinform_label_from_score(0.7) == "mostly_credible"
    assert claimreview.get_coinform_label_from_score(0.5) == "uncertain"
    assert claimreview.get_coinform_label_from_score(0.3) == "not_credible"
    assert claimreview.get_coinform_label_from_score(None) == "not_verifiable"


def test_get_claim_appearances():
    appearances = claimreview.get_claim_appearances(cr_4)
    assert len(appearances) == 1
    assert (
        appearances[0]
        == "https://drschmitz.lettre-medecin-sante.com/coronavirus-lepidemie-est-ailleurs"
    )
    appearances = claimreview.get_claim_appearances(cr_5)
    assert len(appearances) == 7
    assert (
        appearances[0] == "https://www.facebook.com/CorentinFNJ/posts/250959068694828"
    )


def test_get_corrected_url():
    corrected_url = claimreview.get_corrected_url(shortened_cr_url, unshorten=True)
    assert "afp.com" in corrected_url


def test_retrieve_claimreview():
    url = cr_1["url"]
    url, crs = claimreview.retrieve_claimreview(url)
    cr = crs[0]
    assert cr["url"] == cr_1["url"]

    # example using sharethefacts
    url = "https://www.politifact.com/factchecks/2019/may/20/cory-booker/fact-checking-cory-bookers-statistic-about-connect/"
    url, crs = claimreview.retrieve_claimreview(url)
    cr = crs[0]
    assert cr["url"] == url


def test_simplify_label():
    assert claimreview.simplify_label("Credible") == "credible"
    assert claimreview.simplify_label("Credible statement") == "credible"
    assert claimreview.simplify_label("false because it's a lie") == "not_credible"
    assert claimreview.simplify_label("false") == "not_credible"
    assert claimreview.simplify_label("unsupported") == None
