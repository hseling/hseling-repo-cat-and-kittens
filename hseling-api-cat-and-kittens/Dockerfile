FROM hseling/hseling-api-base:python3.6-alpine3.7 as hseling_api_build

LABEL maintainer="Andrea Grillandi <andrea.grillandi@live.it>"

RUN pip install --upgrade pip

RUN mkdir /dependencies
COPY ./hseling-api-cat-and-kittens/requirements.txt /dependencies/requirements.txt
COPY ./hseling-api-cat-and-kittens/setup.py /dependencies/setup.py

RUN apk add --no-cache build-base
RUN apk add --no-cache libstdc++
RUN pip install -r /dependencies/requirements.txt

FROM hseling/hseling-api-base:python3.6-alpine3.7 as production

RUN apk add --no-cache build-base
RUN apk add --no-cache libstdc++
COPY --from=hseling_api_build /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=hseling_api_build /usr/lib/python3.6/site-packages /usr/lib/python3.6/site-packages

COPY --from=hseling_api_build /dependencies /dependencies

COPY ./hseling-lib-cat-and-kittens /dependencies/hseling-lib-cat-and-kittens
RUN pip install /dependencies/hseling-lib-cat-and-kittens

COPY ./hseling-api-cat-and-kittens/hseling_api_cat_and_kittens /app/hseling_api_cat_and_kittens
COPY ./hseling-api-cat-and-kittens/main.py /app/main.py

RUN mkdir -p /data

ENV HSELING_API_CAT_AND_KITTENS_SETTINGS="/app/hseling_api_cat_and_kittens/default_settings.py"

HEALTHCHECK CMD curl --fail http://localhost:5000/healthz || exit 1

