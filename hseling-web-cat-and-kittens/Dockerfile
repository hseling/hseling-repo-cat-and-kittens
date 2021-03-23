FROM hseling/hseling-api-base:python3.6-alpine3.7 as hseling_web_build

LABEL maintainer="Andrea Grillandi <andrea.grillandi@live.it>"

RUN pip install --upgrade pip

RUN apk --no-cache add musl-dev linux-headers g++

RUN mkdir /dependencies
COPY ./hseling-web-cat-and-kittens/requirements.txt /dependencies/requirements.txt
COPY ./hseling-web-cat-and-kittens/setup.py /dependencies/setup.py

RUN pip install -r /dependencies/requirements.txt

FROM hseling/hseling-api-base:python3.6-alpine3.7 as hseling_web_production

COPY --from=hseling_web_build /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=hseling_web_build /usr/lib/python3.6/site-packages /usr/lib/python3.6/site-packages

COPY --from=hseling_web_build /dependencies /dependencies

COPY ./hseling-web-cat-and-kittens/hseling_web_cat_and_kittens /app/hseling_web_cat_and_kittens
COPY ./hseling-web-cat-and-kittens/hseling_web_cat_and_kittens/static /app/static
COPY ./hseling-web-cat-and-kittens/main.py /app/main.py

ENV HSELING_WEB_CAT_AND_KITTENS_SETTINGS="/app/hseling_web_cat_and_kittens/default_settings.py"

HEALTHCHECK CMD curl --fail http://localhost:8000/healthz || exit 1

EXPOSE 8000
